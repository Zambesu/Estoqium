'''Testes dos cálculos do Dashboard.'''
from __future__ import annotations

from pathlib import Path

import pytest

from models import Produto
from services import EstoqueService


@pytest.fixture()
def service(tmp_path: Path) -> EstoqueService:
    return EstoqueService(tmp_path / 'teste.db')


def _produto(**kwargs) -> Produto:
    dados = dict(
        id=None, nome='Produto', categoria='', quantidade=0,
        quantidade_minima=0, preco_custo=0.0, preco_venda=0.0,
    )
    dados.update(kwargs)
    return Produto(**dados)


def test_banco_vazio(service: EstoqueService) -> None:
    assert service.obter_resumo_dashboard() == {
        'produtos_ativos': 0,
        'estoque_baixo': 0,
        'valor_estoque': 0.0,
    }


def test_contagens_e_valor(service: EstoqueService) -> None:
    service.cadastrar_produto(_produto(nome='A', quantidade=10, quantidade_minima=5, preco_custo=4.50))
    service.cadastrar_produto(_produto(nome='B', quantidade=3, quantidade_minima=5, preco_custo=6.00))
    service.cadastrar_produto(_produto(nome='C', quantidade=0, quantidade_minima=2, preco_custo=12.00))

    resumo = service.obter_resumo_dashboard()
    assert resumo['produtos_ativos'] == 3
    assert resumo['estoque_baixo'] == 2  # B (3<=5) e C (0<=2)
    assert resumo['valor_estoque'] == pytest.approx(10 * 4.50 + 3 * 6.00)


def test_estoque_igual_ao_minimo_conta_como_baixo(service: EstoqueService) -> None:
    service.cadastrar_produto(_produto(quantidade=5, quantidade_minima=5))
    assert service.obter_resumo_dashboard()['estoque_baixo'] == 1


def test_produto_inativo_nao_entra_nos_indicadores(service: EstoqueService) -> None:
    produto_id = service.cadastrar_produto(
        _produto(quantidade=0, quantidade_minima=5, preco_custo=10.0)
    )
    service.desativar_produto(produto_id)
    assert service.obter_resumo_dashboard() == {
        'produtos_ativos': 0,
        'estoque_baixo': 0,
        'valor_estoque': 0.0,
    }


def test_movimentacao_atualiza_indicadores(service: EstoqueService) -> None:
    produto_id = service.cadastrar_produto(
        _produto(quantidade=10, quantidade_minima=5, preco_custo=2.00)
    )
    service.registrar_movimentacao(produto_id, 'SAIDA', 6)
    resumo = service.obter_resumo_dashboard()
    assert resumo['estoque_baixo'] == 1
    assert resumo['valor_estoque'] == pytest.approx(4 * 2.00)


def test_lista_reposicao_ordenada(service: EstoqueService) -> None:
    service.cadastrar_produto(_produto(nome='Zerado', quantidade=0, quantidade_minima=2))
    service.cadastrar_produto(_produto(nome='Baixo', quantidade=3, quantidade_minima=5))
    service.cadastrar_produto(_produto(nome='Ok', quantidade=10, quantidade_minima=5))

    reposicao = service.listar_produtos_reposicao()
    assert [p.nome for p in reposicao] == ['Zerado', 'Baixo']


def test_ultimas_movimentacoes(service: EstoqueService) -> None:
    p1 = service.cadastrar_produto(_produto(nome='Arroz', quantidade=10))
    service.cadastrar_produto(_produto(nome='Feijão', quantidade=5))
    service.registrar_movimentacao(p1, 'SAIDA', 2, 'Venda')

    ultimas = service.listar_ultimas_movimentacoes(limite=10)
    assert len(ultimas) == 3
    assert ultimas[0]['tipo'] == 'SAIDA'
    assert ultimas[0]['produto_nome'] == 'Arroz'
    assert ultimas[0]['observacao'] == 'Venda'
    assert ultimas[-1]['tipo'] == 'ENTRADA'

    limitadas = service.listar_ultimas_movimentacoes(limite=1)
    assert len(limitadas) == 1
