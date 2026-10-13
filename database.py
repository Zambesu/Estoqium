from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Iterable, Sequence

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
DEFAULT_DB_PATH = DATA_DIR / 'estoque.db'

SCHEMA = '''
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    categoria TEXT NOT NULL DEFAULT '',
    quantidade INTEGER NOT NULL DEFAULT 0 CHECK (quantidade >= 0),
    quantidade_minima INTEGER NOT NULL DEFAULT 0 CHECK (quantidade_minima >= 0),
    preco_custo REAL NOT NULL DEFAULT 0 CHECK (preco_custo >= 0),
    preco_venda REAL NOT NULL DEFAULT 0 CHECK (preco_venda >= 0),
    data_cadastro TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1))
);

CREATE TABLE IF NOT EXISTS movimentacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id INTEGER NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('ENTRADA', 'SAIDA')),
    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
    data_movimentacao TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    observacao TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (produto_id) REFERENCES produtos (id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_produtos_nome ON produtos (nome);
CREATE INDEX IF NOT EXISTS idx_produtos_ativo ON produtos (ativo);
CREATE INDEX IF NOT EXISTS idx_movimentacoes_produto ON movimentacoes (produto_id);
CREATE INDEX IF NOT EXISTS idx_movimentacoes_data ON movimentacoes (data_movimentacao);
'''


class DatabaseError(Exception):
    '''Erro de acesso ao banco de dados local.'''


def _resolve_db_path(db_path: Path | str | None = None) -> Path:
    return Path(db_path) if db_path is not None else DEFAULT_DB_PATH


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = _resolve_db_path(db_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA foreign_keys = ON;')
        connection.execute('PRAGMA busy_timeout = 30000;')
        return connection
    except (sqlite3.Error, OSError) as exc:
        raise DatabaseError(f'Não foi possível conectar ao banco de dados: {exc}') from exc


def initialize_database(db_path: Path | str | None = None) -> Path:
    path = _resolve_db_path(db_path)
    try:
        with closing(get_connection(path)) as connection:
            with connection:
                connection.executescript(SCHEMA)
    except sqlite3.Error as exc:
        raise DatabaseError(f'Não foi possível inicializar o banco de dados: {exc}') from exc
    return path


def execute_query(
    query: str,
    params: Sequence[object] = (),
    db_path: Path | str | None = None,
) -> list[sqlite3.Row]:
    try:
        with closing(get_connection(db_path)) as connection:
            cursor = connection.execute(query, params)
            return cursor.fetchall()
    except sqlite3.Error as exc:
        raise DatabaseError(f'Erro ao executar consulta: {exc}') from exc


def fetch_one(
    query: str,
    params: Sequence[object] = (),
    db_path: Path | str | None = None,
) -> sqlite3.Row | None:
    try:
        with closing(get_connection(db_path)) as connection:
            cursor = connection.execute(query, params)
            return cursor.fetchone()
    except sqlite3.Error as exc:
        raise DatabaseError(f'Erro ao executar consulta: {exc}') from exc


def execute_write(
    query: str,
    params: Sequence[object] = (),
    db_path: Path | str | None = None,
) -> int:
    try:
        with closing(get_connection(db_path)) as connection:
            with connection:
                cursor = connection.execute(query, params)
                if query.lstrip().upper().startswith('INSERT'):
                    return int(cursor.lastrowid)
                return cursor.rowcount
    except sqlite3.Error as exc:
        raise DatabaseError(f'Erro ao gravar no banco de dados: {exc}') from exc


def execute_many(
    query: str,
    params_list: Iterable[Sequence[object]],
    db_path: Path | str | None = None,
) -> int:
    try:
        with closing(get_connection(db_path)) as connection:
            with connection:
                cursor = connection.executemany(query, params_list)
                return cursor.rowcount
    except sqlite3.Error as exc:
        raise DatabaseError(f'Erro ao gravar no banco de dados: {exc}') from exc


def execute_transaction(
    statements: Iterable[tuple[str, Sequence[object]]],
    db_path: Path | str | None = None,
) -> None:
    try:
        with closing(get_connection(db_path)) as connection:
            with connection:
                for query, params in statements:
                    connection.execute(query, params)
    except sqlite3.Error as exc:
        raise DatabaseError(f'Erro ao executar transação: {exc}') from exc


def backup_database(destino: Path | str, db_path: Path | str | None = None) -> Path:
    '''Cria uma cópia consistente do banco usando a API de backup do SQLite.'''
    origem = _resolve_db_path(db_path)
    destino_path = Path(destino)
    destino_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with closing(get_connection(origem)) as source, closing(
            sqlite3.connect(destino_path, timeout=30)
        ) as target:
            source.backup(target)
    except sqlite3.Error as exc:
        raise DatabaseError(f'Não foi possível criar o backup: {exc}') from exc
    return destino_path


def validate_sqlite_file(caminho: Path | str) -> None:
    '''Garante que o arquivo é um banco SQLite íntegro e com o schema do Estoqium.'''
    path = Path(caminho)
    if not path.is_file():
        raise DatabaseError('O arquivo selecionado não existe.')

    try:
        connection = sqlite3.connect(f'file:{path}?mode=ro', uri=True, timeout=30)
    except sqlite3.Error as exc:
        raise DatabaseError(f'Não foi possível abrir o arquivo: {exc}') from exc

    try:
        with closing(connection) as conn:
            integridade = conn.execute('PRAGMA integrity_check;').fetchone()
            if integridade is None or integridade[0] != 'ok':
                raise DatabaseError('O arquivo não passou na verificação de integridade.')

            tabelas = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table';"
                )
            }
            if not {'produtos', 'movimentacoes'} <= tabelas:
                raise DatabaseError(
                    'O arquivo não contém as tabelas do Estoqium (produtos/movimentacoes).'
                )
    except sqlite3.Error as exc:
        raise DatabaseError(f'O arquivo não é um banco SQLite válido: {exc}') from exc


def restore_database(origem: Path | str, db_path: Path | str | None = None) -> Path:
    '''Restaura um backup validado, preservando o banco atual em caso de falha.'''
    destino = _resolve_db_path(db_path)
    validate_sqlite_file(origem)

    copia_seguranca = destino.with_suffix('.restore-backup')
    try:
        if destino.exists():
            with closing(get_connection(destino)) as source, closing(
                sqlite3.connect(copia_seguranca, timeout=30)
            ) as target:
                source.backup(target)

        with closing(sqlite3.connect(origem, timeout=30)) as source, closing(
            sqlite3.connect(destino, timeout=30)
        ) as target:
            source.backup(target)
            target.execute('PRAGMA foreign_keys = ON;')
    except (sqlite3.Error, OSError) as exc:
        if copia_seguranca.exists():
            try:
                with closing(sqlite3.connect(copia_seguranca, timeout=30)) as source, closing(
                    sqlite3.connect(destino, timeout=30)
                ) as target:
                    source.backup(target)
            except sqlite3.Error:
                pass
        raise DatabaseError(
            f'Falha ao restaurar o backup; o banco atual foi preservado: {exc}'
        ) from exc
    finally:
        copia_seguranca.unlink(missing_ok=True)

    return destino
