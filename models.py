from dataclasses import dataclass


@dataclass(slots=True)
class Produto:
    id: int | None
    nome: str
    categoria: str
    quantidade: int
    quantidade_minima: int
    preco_custo: float
    preco_venda: float
    data_cadastro: str | None = None
    ativo: bool = True


@dataclass(slots=True)
class Movimentacao:
    id: int | None
    produto_id: int
    tipo: str
    quantidade: int
    data_movimentacao: str | None = None
    observacao: str = ''
