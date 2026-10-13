'''Testes de backup e restauração do banco de dados.'''
from __future__ import annotations

from pathlib import Path

import pytest

from database import (
    DatabaseError,
    backup_database,
    restore_database,
    validate_sqlite_file,
)
from models import Produto
from services import EstoqueService


@pytest.fixture()
def ambiente(tmp_path: Path) -> tuple[EstoqueService, Path, Path]:
    db_path = tmp_path / 'estoque.db'
    service = EstoqueService(db_path)
    service.cadastrar_produto(Produto(None, 'Arroz', 'Alimentos', 10, 5, 4.50, 7.90))
    service.cadastrar_produto(Produto(None, 'Feijão', 'Alimentos', 3, 5, 6.00, 9.90))
    return service, db_path, tmp_path


def test_backup_cria_copia_valida(ambiente) -> None:
    _, db_path, tmp_path = ambiente
    backup = backup_database(tmp_path / 'backup.db', db_path)
    assert backup.is_file()
    validate_sqlite_file(backup)


def test_restauracao_recupera_dados(ambiente) -> None:
    _, db_path, tmp_path = ambiente
    backup = backup_database(tmp_path / 'backup.db', db_path)

    destino = tmp_path / 'restaurado.db'
    restore_database(backup, destino)
    service = EstoqueService(destino)
    assert [p.nome for p in service.listar_produtos()] == ['Arroz', 'Feijão']


def test_restauracao_substitui_dados_atuais(ambiente) -> None:
    service, db_path, tmp_path = ambiente
    backup = backup_database(tmp_path / 'backup.db', db_path)

    service.cadastrar_produto(Produto(None, 'Café', 'Bebidas', 1, 1, 9.0, 15.0))
    restore_database(backup, db_path)

    reaberto = EstoqueService(db_path)
    assert [p.nome for p in reaberto.listar_produtos()] == ['Arroz', 'Feijão']


def test_arquivo_invalido_nao_corrompe_banco_atual(ambiente) -> None:
    _, db_path, tmp_path = ambiente
    lixo = tmp_path / 'lixo.db'
    lixo.write_text('isso não é sqlite', encoding='utf-8')

    with pytest.raises(DatabaseError):
        restore_database(lixo, db_path)

    service = EstoqueService(db_path)
    assert len(service.listar_produtos()) == 2  # banco preservado


def test_arquivo_inexistente_e_rejeitado(ambiente) -> None:
    _, db_path, tmp_path = ambiente
    with pytest.raises(DatabaseError, match='não existe'):
        restore_database(tmp_path / 'nao_existe.db', db_path)


def test_sqlite_sem_schema_do_estoqium_e_rejeitado(ambiente) -> None:
    import sqlite3

    _, db_path, tmp_path = ambiente
    outro = tmp_path / 'outro.db'
    with sqlite3.connect(outro) as conn:
        conn.execute('CREATE TABLE qualquer (id INTEGER);')

    with pytest.raises(DatabaseError, match='tabelas do Estoqium'):
        restore_database(outro, db_path)


def test_nao_deixa_arquivo_temporario(ambiente) -> None:
    _, db_path, tmp_path = ambiente
    backup = backup_database(tmp_path / 'backup.db', db_path)
    restore_database(backup, db_path)
    assert not db_path.with_suffix('.restore-backup').exists()
