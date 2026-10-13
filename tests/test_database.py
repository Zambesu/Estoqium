'''Testes de inicialização e estrutura do banco de dados.'''
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from database import (
    DatabaseError,
    execute_query,
    get_connection,
    initialize_database,
)


def test_inicializacao_cria_arquivo_e_tabelas(tmp_path: Path) -> None:
    db_path = initialize_database(tmp_path / 'dados' / 'estoque.db')

    assert db_path.is_file()
    with get_connection(db_path) as conn:
        tabelas = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table';"
            )
        }
    assert {'produtos', 'movimentacoes'} <= tabelas


def test_inicializacao_e_idempotente(tmp_path: Path) -> None:
    db_path = tmp_path / 'estoque.db'
    initialize_database(db_path)
    initialize_database(db_path)  # não deve falhar nem apagar dados

    with get_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO produtos (nome) VALUES ('Produto teste');"
        )
        conn.commit()
    initialize_database(db_path)
    rows = execute_query('SELECT nome FROM produtos;', db_path=db_path)
    assert len(rows) == 1


def test_chaves_estrangeiras_ativas(tmp_path: Path) -> None:
    db_path = initialize_database(tmp_path / 'estoque.db')
    with get_connection(db_path) as conn:
        ativo = conn.execute('PRAGMA foreign_keys;').fetchone()[0]
    assert ativo == 1


def test_movimentacao_de_produto_inexistente_falha(tmp_path: Path) -> None:
    db_path = initialize_database(tmp_path / 'estoque.db')
    with pytest.raises(sqlite3.IntegrityError):
        with get_connection(db_path) as conn:
            conn.execute(
                "INSERT INTO movimentacoes (produto_id, tipo, quantidade) "
                "VALUES (999, 'ENTRADA', 1);"
            )


def test_caminho_invalido_gera_erro_compreensivel() -> None:
    with pytest.raises(DatabaseError, match='banco de dados'):
        initialize_database(Path('Z:\\caminho\\inexistente\\estoque.db'))
