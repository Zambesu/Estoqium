from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Sequence

from database import DEFAULT_DB_PATH, DatabaseError, execute_query

Row = Sequence[object]
Report = tuple[str, list[str], list[Row]]


class ReportService:
    '''Camada responsável pelos relatórios e exportações do Estoqium.'''

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)

    def produtos_ativos(self) -> Report:
        rows = execute_query(
            '''
            SELECT id, nome, categoria, quantidade, quantidade_minima,
                   preco_custo, preco_venda, data_cadastro
              FROM produtos
             WHERE ativo = 1
             ORDER BY nome COLLATE NOCASE;
            ''',
            db_path=self.db_path,
        )
        headers = [
            'Código', 'Nome', 'Categoria', 'Quantidade', 'Estoque mínimo',
            'Preço de custo', 'Preço de venda', 'Data de cadastro',
        ]
        data: list[Row] = [
            (
                row['id'], row['nome'], row['categoria'], row['quantidade'],
                row['quantidade_minima'], _moeda(row['preco_custo']),
                _moeda(row['preco_venda']), row['data_cadastro'],
            )
            for row in rows
        ]
        return ('Relatório de produtos ativos', headers, data)

    def estoque_baixo(self) -> Report:
        rows = execute_query(
            '''
            SELECT id, nome, categoria, quantidade, quantidade_minima, preco_custo
              FROM produtos
             WHERE ativo = 1 AND quantidade <= quantidade_minima
             ORDER BY quantidade ASC, nome COLLATE NOCASE;
            ''',
            db_path=self.db_path,
        )
        headers = [
            'Código', 'Nome', 'Categoria', 'Quantidade', 'Estoque mínimo', 'Preço de custo',
        ]
        data: list[Row] = [
            (
                row['id'], row['nome'], row['categoria'], row['quantidade'],
                row['quantidade_minima'], _moeda(row['preco_custo']),
            )
            for row in rows
        ]
        return ('Relatório de produtos com estoque baixo', headers, data)

    def movimentacoes(self, data_inicio: str = '', data_fim: str = '') -> Report:
        query = '''
            SELECT m.id, p.nome AS produto, m.tipo, m.quantidade,
                   m.data_movimentacao, m.observacao
              FROM movimentacoes m
              INNER JOIN produtos p ON p.id = m.produto_id
        '''
        conditions: list[str] = []
        params: list[object] = []
        if data_inicio:
            conditions.append('date(m.data_movimentacao) >= date(?)')
            params.append(data_inicio)
        if data_fim:
            conditions.append('date(m.data_movimentacao) <= date(?)')
            params.append(data_fim)
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY m.data_movimentacao DESC, m.id DESC;'

        rows = execute_query(query, params, self.db_path)
        headers = ['Código', 'Produto', 'Tipo', 'Quantidade', 'Data', 'Observação']
        data: list[Row] = [
            (
                row['id'], row['produto'],
                'Entrada' if row['tipo'] == 'ENTRADA' else 'Saída',
                row['quantidade'], row['data_movimentacao'], row['observacao'],
            )
            for row in rows
        ]
        titulo = 'Histórico de entradas e saídas'
        if data_inicio or data_fim:
            titulo += f' (período: {data_inicio or "início"} a {data_fim or "hoje"})'
        return (titulo, headers, data)

    def valor_estoque(self) -> Report:
        rows = execute_query(
            '''
            SELECT id, nome, categoria, quantidade, preco_custo,
                   quantidade * preco_custo AS valor_total
              FROM produtos
             WHERE ativo = 1
             ORDER BY nome COLLATE NOCASE;
            ''',
            db_path=self.db_path,
        )
        headers = [
            'Código', 'Nome', 'Categoria', 'Quantidade', 'Preço de custo', 'Valor total',
        ]
        data: list[Row] = [
            (
                row['id'], row['nome'], row['categoria'], row['quantidade'],
                _moeda(row['preco_custo']), _moeda(row['valor_total']),
            )
            for row in rows
        ]
        total = sum(float(row['valor_total']) for row in rows)
        data.append(('', '', '', '', 'TOTAL GERAL', _moeda(total)))
        return ('Relatório de valor estimado do estoque', headers, data)

    def exportar_csv(self, caminho: Path | str, report: Report) -> Path:
        titulo, headers, data = report
        path = Path(caminho)
        try:
            with path.open('w', newline='', encoding='utf-8-sig') as arquivo:
                writer = csv.writer(arquivo, delimiter=';')
                writer.writerow([titulo])
                writer.writerow([f'Gerado em: {datetime.now():%d/%m/%Y %H:%M}'])
                writer.writerow([])
                writer.writerow(headers)
                writer.writerows(data)
        except OSError as exc:
            raise DatabaseError(f'Não foi possível salvar o arquivo CSV: {exc}') from exc
        return path

    def exportar_txt(self, caminho: Path | str, report: Report) -> Path:
        titulo, headers, data = report
        path = Path(caminho)
        larguras = _larguras_colunas(headers, data)
        linha_separadora = '-+-'.join('-' * largura for largura in larguras)

        try:
            with path.open('w', encoding='utf-8') as arquivo:
                arquivo.write(titulo + '\n')
                arquivo.write(f'Gerado em: {datetime.now():%d/%m/%Y %H:%M}\n\n')
                arquivo.write(_formatar_linha(headers, larguras) + '\n')
                arquivo.write(linha_separadora + '\n')
                for row in data:
                    arquivo.write(_formatar_linha(row, larguras) + '\n')
                arquivo.write(f'\nTotal de registros: {len(data)}\n')
        except OSError as exc:
            raise DatabaseError(f'Não foi possível salvar o arquivo TXT: {exc}') from exc
        return path


def _moeda(valor: object) -> str:
    return f'{float(valor):.2f}'.replace('.', ',')


def _larguras_colunas(headers: list[str], data: list[Row]) -> list[int]:
    larguras = [len(h) for h in headers]
    for row in data:
        for i, valor in enumerate(row):
            larguras[i] = max(larguras[i], len(str(valor)))
    return [min(largura, 60) for largura in larguras]


def _formatar_linha(valores: Sequence[object], larguras: list[int]) -> str:
    return ' | '.join(
        str(valor)[:largura].ljust(largura) for valor, largura in zip(valores, larguras)
    )
