'''Testes de geração e exportação de relatórios.'''
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from database import DatabaseError
from models import Produto
from reports import ReportService
from services import EstoqueService


@pytest.fixture()
def services(tmp_path: Path) -> tuple[EstoqueService, ReportService, Path]:
    db_path = tmp_path / 'teste.db'
    service = EstoqueService(db_path)
    p1 = service.cadastrar_produto(
        Produto(None, 'Açúcar Refinado', 'Alimentos', 10, 5, 4.50, 7.90)
    )
    service.cadastrar_produto(
        Produto(None, 'Feijão Carioca', 'Alimentos', 3, 5, 6.00, 9.90)
    )
    service.registrar_movimentacao(p1, 'SAIDA', 2, 'Venda balcão')
    return service, ReportService(db_path), tmp_path


def test_relatorio_produtos_ativos(services) -> None:
    _, reports, _ = services
    titulo, headers, data = reports.produtos_ativos()
    assert 'produtos ativos' in titulo
    assert 'Nome' in headers and 'Preço de custo' in headers
    assert len(data) == 2


def test_relatorio_estoque_baixo(services) -> None:
    _, reports, _ = services
    _, _, data = reports.estoque_baixo()
    assert len(data) == 1
    assert data[0][1] == 'Feijão Carioca'


def test_relatorio_movimentacoes_com_filtro(services) -> None:
    _, reports, _ = services
    _, _, data = reports.movimentacoes()
    assert len(data) == 3  # 2 entradas iniciais + 1 saída

    titulo, _, vazio = reports.movimentacoes(data_inicio='2099-01-01')
    assert vazio == []
    assert 'período' in titulo


def test_relatorio_valor_estoque(services) -> None:
    _, reports, _ = services
    _, _, data = reports.valor_estoque()
    assert data[-1][-2] == 'TOTAL GERAL'
    assert data[-1][-1] == '54,00'  # 8*4,50 + 3*6,00


def test_exportacao_csv_com_acentos(services) -> None:
    _, reports, tmp_path = services
    caminho = reports.exportar_csv(tmp_path / 'ativos.csv', reports.produtos_ativos())

    raw = caminho.read_bytes()
    assert raw.startswith(b'\xef\xbb\xbf')  # BOM para Excel
    texto = raw.decode('utf-8-sig')
    assert 'Açúcar Refinado' in texto
    assert 'Relatório de produtos ativos' in texto

    linhas = list(csv.reader(texto.splitlines(), delimiter=';'))
    assert linhas[3][0] == 'Código'
    assert len(linhas) == 3 + 1 + 2  # cabeçalho (3) + linha de headers + 2 produtos


def test_exportacao_txt_formatada(services) -> None:
    _, reports, tmp_path = services
    caminho = reports.exportar_txt(tmp_path / 'movs.txt', reports.movimentacoes())

    texto = caminho.read_text(encoding='utf-8')
    assert 'Histórico de entradas e saídas' in texto
    assert 'Venda balcão' in texto
    assert 'Total de registros: 3' in texto


def test_exportacao_em_diretorio_inexistente_falha(services) -> None:
    _, reports, tmp_path = services
    with pytest.raises(DatabaseError, match='CSV'):
        reports.exportar_csv(
            tmp_path / 'inexistente' / 'x.csv', reports.produtos_ativos()
        )
