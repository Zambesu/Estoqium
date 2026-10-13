from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from database import (
    DEFAULT_DB_PATH,
    DatabaseError,
    execute_query,
    execute_write,
    fetch_one,
    get_connection,
    initialize_database,
)
from models import Movimentacao, Produto


class EstoqueService:
    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        initialize_database(self.db_path)

    def listar_produtos(
        self,
        termo: str = '',
        categoria: str = '',
        situacao: str = 'ATIVOS',
    ) -> list[Produto]:
        query = 'SELECT * FROM produtos'
        conditions: list[str] = []
        params: list[object] = []

        if situacao == 'ATIVOS':
            conditions.append('ativo = 1')
        elif situacao == 'INATIVOS':
            conditions.append('ativo = 0')

        if categoria and categoria != 'Todas':
            conditions.append('categoria = ?')
            params.append(categoria)

        if termo:
            conditions.append('(nome LIKE ? OR CAST(id AS TEXT) = ?)')
            params.extend([f'%{termo}%', termo])

        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY nome COLLATE NOCASE;'

        rows = execute_query(query, params, self.db_path)
        return [self._row_to_produto(row) for row in rows]

    def listar_categorias(self) -> list[str]:
        rows = execute_query(
            "SELECT DISTINCT categoria FROM produtos WHERE categoria <> '' ORDER BY categoria COLLATE NOCASE;",
            db_path=self.db_path,
        )
        return [str(row['categoria']) for row in rows]

    def obter_produto(self, produto_id: int) -> Produto | None:
        row = fetch_one(
            'SELECT * FROM produtos WHERE id = ?;',
            (produto_id,),
            self.db_path,
        )
        return self._row_to_produto(row) if row else None

    def cadastrar_produto(self, produto: Produto) -> int:
        self._validar_produto(produto, validar_quantidade=True)

        try:
            with closing(get_connection(self.db_path)) as connection:
                with connection:
                    cursor = connection.execute(
                        '''
                        INSERT INTO produtos (
                            nome, categoria, quantidade, quantidade_minima,
                            preco_custo, preco_venda, ativo
                        ) VALUES (?, ?, ?, ?, ?, ?, 1);
                        ''',
                        (
                            produto.nome,
                            produto.categoria,
                            produto.quantidade,
                            produto.quantidade_minima,
                            produto.preco_custo,
                            produto.preco_venda,
                        ),
                    )
                    produto_id = int(cursor.lastrowid)

                    if produto.quantidade > 0:
                        connection.execute(
                            '''
                            INSERT INTO movimentacoes (
                                produto_id, tipo, quantidade, observacao
                            ) VALUES (?, 'ENTRADA', ?, ?);
                            ''',
                            (
                                produto_id,
                                produto.quantidade,
                                'Cadastro inicial do produto',
                            ),
                        )
                    return produto_id
        except sqlite3.Error as exc:
            raise DatabaseError(f'Erro ao cadastrar produto: {exc}') from exc

    def atualizar_produto(self, produto: Produto) -> None:
        if produto.id is None:
            raise ValueError('Selecione um produto para editar.')
        self._validar_produto(produto, validar_quantidade=False)

        execute_write(
            '''
            UPDATE produtos
               SET nome = ?,
                   categoria = ?,
                   quantidade_minima = ?,
                   preco_custo = ?,
                   preco_venda = ?,
                   ativo = ?
             WHERE id = ?;
            ''',
            (
                produto.nome,
                produto.categoria,
                produto.quantidade_minima,
                produto.preco_custo,
                produto.preco_venda,
                1 if produto.ativo else 0,
                produto.id,
            ),
            self.db_path,
        )

    def desativar_produto(self, produto_id: int) -> None:
        execute_write(
            'UPDATE produtos SET ativo = 0 WHERE id = ?;',
            (produto_id,),
            self.db_path,
        )

    def reativar_produto(self, produto_id: int) -> None:
        execute_write(
            'UPDATE produtos SET ativo = 1 WHERE id = ?;',
            (produto_id,),
            self.db_path,
        )

    def registrar_movimentacao(
        self,
        produto_id: int,
        tipo: str,
        quantidade: int,
        observacao: str = '',
    ) -> int:
        tipo_normalizado = tipo.strip().upper()
        if tipo_normalizado not in {'ENTRADA', 'SAIDA'}:
            raise ValueError('Tipo de movimentação inválido.')
        if quantidade <= 0:
            raise ValueError('A quantidade movimentada deve ser um inteiro positivo.')

        try:
            with closing(get_connection(self.db_path)) as connection:
                with connection:
                    produto = connection.execute(
                        'SELECT id, quantidade, ativo FROM produtos WHERE id = ?;',
                        (produto_id,),
                    ).fetchone()

                    if produto is None:
                        raise ValueError('Produto não encontrado.')
                    if not bool(produto['ativo']):
                        raise ValueError('Não é possível movimentar um produto inativo.')

                    estoque_atual = int(produto['quantidade'])
                    if tipo_normalizado == 'SAIDA' and quantidade > estoque_atual:
                        raise ValueError('A saída não pode ser maior que o estoque disponível.')

                    nova_quantidade = (
                        estoque_atual + quantidade
                        if tipo_normalizado == 'ENTRADA'
                        else estoque_atual - quantidade
                    )

                    connection.execute(
                        'UPDATE produtos SET quantidade = ? WHERE id = ?;',
                        (nova_quantidade, produto_id),
                    )
                    cursor = connection.execute(
                        '''
                        INSERT INTO movimentacoes (
                            produto_id, tipo, quantidade, observacao
                        ) VALUES (?, ?, ?, ?);
                        ''',
                        (produto_id, tipo_normalizado, quantidade, observacao.strip()),
                    )
                    return int(cursor.lastrowid)
        except sqlite3.Error as exc:
            raise DatabaseError(f'Erro ao registrar movimentação: {exc}') from exc

    def listar_movimentacoes(
        self,
        produto_id: int | None = None,
        tipo: str = 'TODOS',
        data_inicio: str = '',
        data_fim: str = '',
    ) -> list[Movimentacao]:
        query = '''
            SELECT m.id,
                   m.produto_id,
                   m.tipo,
                   m.quantidade,
                   m.data_movimentacao,
                   m.observacao
              FROM movimentacoes m
              INNER JOIN produtos p ON p.id = m.produto_id
        '''
        conditions: list[str] = []
        params: list[object] = []

        if produto_id is not None:
            conditions.append('m.produto_id = ?')
            params.append(produto_id)

        tipo_normalizado = tipo.strip().upper()
        if tipo_normalizado in {'ENTRADA', 'SAIDA'}:
            conditions.append('m.tipo = ?')
            params.append(tipo_normalizado)

        if data_inicio:
            conditions.append("date(m.data_movimentacao) >= date(?)")
            params.append(data_inicio)
        if data_fim:
            conditions.append("date(m.data_movimentacao) <= date(?)")
            params.append(data_fim)

        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY m.data_movimentacao DESC, m.id DESC;'

        rows = execute_query(query, params, self.db_path)
        return [self._row_to_movimentacao(row) for row in rows]

    def _validar_produto(self, produto: Produto, validar_quantidade: bool) -> None:
        if not produto.nome.strip():
            raise ValueError('Informe o nome do produto.')
        if validar_quantidade and produto.quantidade < 0:
            raise ValueError('A quantidade inicial não pode ser negativa.')
        if produto.quantidade_minima < 0:
            raise ValueError('O estoque mínimo não pode ser negativo.')
        if produto.preco_custo < 0:
            raise ValueError('O preço de custo não pode ser negativo.')
        if produto.preco_venda < 0:
            raise ValueError('O preço de venda não pode ser negativo.')

    def _row_to_produto(self, row) -> Produto:
        return Produto(
            id=int(row['id']),
            nome=str(row['nome']),
            categoria=str(row['categoria']),
            quantidade=int(row['quantidade']),
            quantidade_minima=int(row['quantidade_minima']),
            preco_custo=float(row['preco_custo']),
            preco_venda=float(row['preco_venda']),
            data_cadastro=str(row['data_cadastro']),
            ativo=bool(row['ativo']),
        )

    def _row_to_movimentacao(self, row) -> Movimentacao:
        return Movimentacao(
            id=int(row['id']),
            produto_id=int(row['produto_id']),
            tipo=str(row['tipo']),
            quantidade=int(row['quantidade']),
            data_movimentacao=str(row['data_movimentacao']),
            observacao=str(row['observacao']),
        )
