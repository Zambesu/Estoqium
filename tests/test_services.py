'''Testes das regras de negócio de produtos e movimentações.'''
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
        id=None, nome='Arroz', categoria='Alimentos', quantidade=10,
        quantidade_minima=5, preco_custo=4.50, preco_venda=7.90,
    )
    dados.update(kwargs)
    return Produto(**dados)


class TestProdutos:
    def test_cadastro_e_listagem(self, service: EstoqueService) -> None:
        produto_id = service.cadastrar_produto(_produto())
        produtos = service.listar_produtos()
        assert len(produtos) == 1
        assert produtos[0].id == produto_id
        assert produtos[0].nome == 'Arroz'

    def test_cadastro_com_quantidade_gera_movimentacao_inicial(
        self, service: EstoqueService
    ) -> None:
        service.cadastrar_produto(_produto(quantidade=7))
        movs = service.listar_movimentacoes()
        assert len(movs) == 1
        assert movs[0].tipo == 'ENTRADA' and movs[0].quantidade == 7

    def test_cadastro_sem_quantidade_nao_gera_movimentacao(
        self, service: EstoqueService
    ) -> None:
        service.cadastrar_produto(_produto(quantidade=0))
        assert service.listar_movimentacoes() == []

    def test_edicao_de_produto(self, service: EstoqueService) -> None:
        produto_id = service.cadastrar_produto(_produto())
        editado = _produto(id=produto_id, nome='Arroz Integral', preco_custo=5.00)
        service.atualizar_produto(editado)
        produto = service.obter_produto(produto_id)
        assert produto is not None
        assert produto.nome == 'Arroz Integral'
        assert produto.preco_custo == 5.00
        assert produto.quantidade == 10  # edição não altera estoque

    def test_desativar_e_reativar(self, service: EstoqueService) -> None:
        produto_id = service.cadastrar_produto(_produto())
        service.desativar_produto(produto_id)
        assert service.listar_produtos() == []
        assert len(service.listar_produtos(situacao='INATIVOS')) == 1
        service.reativar_produto(produto_id)
        assert len(service.listar_produtos()) == 1

    def test_pesquisa_por_nome(self, service: EstoqueService) -> None:
        service.cadastrar_produto(_produto(nome='Feijão Carioca'))
        service.cadastrar_produto(_produto(nome='Arroz Branco'))
        resultado = service.listar_produtos(termo='feijão')
        assert [p.nome for p in resultado] == ['Feijão Carioca']


class TestValidacoes:
    @pytest.mark.parametrize(
        'campo, valor, mensagem',
        [
            ('nome', '   ', 'nome'),
            ('quantidade', -1, 'quantidade inicial'),
            ('quantidade_minima', -1, 'estoque mínimo'),
            ('preco_custo', -0.01, 'preço de custo'),
            ('preco_venda', -0.01, 'preço de venda'),
        ],
    )
    def test_valores_invalidos_sao_rejeitados(
        self, service: EstoqueService, campo: str, valor, mensagem: str
    ) -> None:
        with pytest.raises(ValueError, match=mensagem):
            service.cadastrar_produto(_produto(**{campo: valor}))

    def test_edicao_sem_id_falha(self, service: EstoqueService) -> None:
        with pytest.raises(ValueError, match='Selecione um produto'):
            service.atualizar_produto(_produto())


class TestMovimentacoes:
    def test_entrada_soma_estoque(self, service: EstoqueService) -> None:
        produto_id = service.cadastrar_produto(_produto(quantidade=10))
        service.registrar_movimentacao(produto_id, 'ENTRADA', 5)
        produto = service.obter_produto(produto_id)
        assert produto is not None and produto.quantidade == 15

    def test_saida_subtrai_estoque(self, service: EstoqueService) -> None:
        produto_id = service.cadastrar_produto(_produto(quantidade=10))
        service.registrar_movimentacao(produto_id, 'SAIDA', 4)
        produto = service.obter_produto(produto_id)
        assert produto is not None and produto.quantidade == 6

    def test_saida_maior_que_estoque_e_bloqueada(
        self, service: EstoqueService
    ) -> None:
        produto_id = service.cadastrar_produto(_produto(quantidade=3))
        with pytest.raises(ValueError, match='maior que o estoque'):
            service.registrar_movimentacao(produto_id, 'SAIDA', 4)
        produto = service.obter_produto(produto_id)
        assert produto is not None and produto.quantidade == 3  # sem efeito colateral

    def test_estoque_nunca_fica_negativo(self, service: EstoqueService) -> None:
        produto_id = service.cadastrar_produto(_produto(quantidade=2))
        service.registrar_movimentacao(produto_id, 'SAIDA', 2)
        with pytest.raises(ValueError):
            service.registrar_movimentacao(produto_id, 'SAIDA', 1)
        produto = service.obter_produto(produto_id)
        assert produto is not None and produto.quantidade == 0

    def test_movimentacao_em_produto_inativo_e_bloqueada(
        self, service: EstoqueService
    ) -> None:
        produto_id = service.cadastrar_produto(_produto())
        service.desativar_produto(produto_id)
        with pytest.raises(ValueError, match='inativo'):
            service.registrar_movimentacao(produto_id, 'ENTRADA', 1)

    def test_movimentacao_em_produto_inexistente(
        self, service: EstoqueService
    ) -> None:
        with pytest.raises(ValueError, match='não encontrado'):
            service.registrar_movimentacao(999, 'ENTRADA', 1)

    @pytest.mark.parametrize('tipo', ['entrada', 'saida'])
    def test_tipo_e_normalizado(self, service: EstoqueService, tipo: str) -> None:
        produto_id = service.cadastrar_produto(_produto(quantidade=10))
        service.registrar_movimentacao(produto_id, tipo, 1)
        movs = service.listar_movimentacoes()
        assert movs[0].tipo == tipo.upper()

    def test_tipo_invalido_e_rejeitado(self, service: EstoqueService) -> None:
        produto_id = service.cadastrar_produto(_produto())
        with pytest.raises(ValueError, match='inválido'):
            service.registrar_movimentacao(produto_id, 'TRANSFERENCIA', 1)

    def test_quantidade_invalida_e_rejeitada(self, service: EstoqueService) -> None:
        produto_id = service.cadastrar_produto(_produto())
        with pytest.raises(ValueError, match='positivo'):
            service.registrar_movimentacao(produto_id, 'ENTRADA', 0)

    def test_consistencia_movimentacoes_e_estoque(
        self, service: EstoqueService
    ) -> None:
        produto_id = service.cadastrar_produto(_produto(quantidade=10))
        service.registrar_movimentacao(produto_id, 'ENTRADA', 5)
        service.registrar_movimentacao(produto_id, 'SAIDA', 3)
        service.registrar_movimentacao(produto_id, 'SAIDA', 2)

        movs = service.listar_movimentacoes(produto_id=produto_id)
        saldo = sum(
            m.quantidade if m.tipo == 'ENTRADA' else -m.quantidade for m in movs
        )
        produto = service.obter_produto(produto_id)
        assert produto is not None
        assert produto.quantidade == saldo == 10

    def test_filtro_por_tipo_e_periodo(self, service: EstoqueService) -> None:
        produto_id = service.cadastrar_produto(_produto(quantidade=10))
        service.registrar_movimentacao(produto_id, 'SAIDA', 1)
        assert len(service.listar_movimentacoes(tipo='SAIDA')) == 1
        assert len(service.listar_movimentacoes(tipo='ENTRADA')) == 1
        assert service.listar_movimentacoes(data_inicio='2099-01-01') == []


class TestPersistencia:
    def test_dados_sobrevivem_a_reabertura(self, tmp_path: Path) -> None:
        db_path = tmp_path / 'teste.db'
        service = EstoqueService(db_path)
        produto_id = service.cadastrar_produto(_produto())
        service.registrar_movimentacao(produto_id, 'SAIDA', 3)
        del service

        reaberto = EstoqueService(db_path)
        produto = reaberto.obter_produto(produto_id)
        assert produto is not None and produto.quantidade == 7
        assert len(reaberto.listar_movimentacoes()) == 2
