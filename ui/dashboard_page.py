from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from database import DatabaseError
from services import EstoqueService


class DashboardPage(tk.Frame):
    CONTENT_BG = '#f8fafc'
    TEXT_COLOR = '#0f172a'
    TEXT_MUTED = '#64748b'
    PRIMARY = '#2563eb'
    WARNING = '#d97706'
    SUCCESS = '#16a34a'

    def __init__(self, master: tk.Misc, service: EstoqueService) -> None:
        super().__init__(master, bg=self.CONTENT_BG)
        self.service = service

        self._build_cards()
        self._build_tables()
        self.refresh()

    def _build_cards(self) -> None:
        cards = tk.Frame(self, bg=self.CONTENT_BG)
        cards.pack(fill='x', padx=28, pady=(24, 12))

        for column in range(3):
            cards.grid_columnconfigure(column, weight=1, uniform='cards')

        self.card_produtos = self._create_card(
            cards, 0, 'Produtos ativos', self.PRIMARY,
            'Itens disponíveis para movimentação',
        )
        self.card_baixo = self._create_card(
            cards, 1, 'Estoque baixo', self.WARNING,
            'Quantidade menor ou igual ao estoque mínimo',
        )
        self.card_valor = self._create_card(
            cards, 2, 'Valor estimado do estoque', self.SUCCESS,
            'Quantidade disponível x preço de custo',
        )

    def _create_card(
        self,
        master: tk.Frame,
        column: int,
        titulo: str,
        cor: str,
        subtitulo: str,
    ) -> dict[str, tk.Label]:
        card = tk.Frame(
            master,
            bg='white',
            highlightbackground='#e2e8f0',
            highlightthickness=1,
            padx=18,
            pady=16,
        )
        card.grid(row=0, column=column, sticky='nsew', padx=(0 if column == 0 else 8, 0))

        tk.Label(
            card,
            text=titulo,
            font=('Segoe UI', 10, 'bold'),
            bg='white',
            fg=self.TEXT_MUTED,
        ).pack(anchor='w')

        valor = tk.Label(
            card,
            text='0',
            font=('Segoe UI', 24, 'bold'),
            bg='white',
            fg=cor,
        )
        valor.pack(anchor='w', pady=(6, 2))

        tk.Label(
            card,
            text=subtitulo,
            font=('Segoe UI', 8),
            bg='white',
            fg=self.TEXT_MUTED,
            wraplength=260,
            justify='left',
        ).pack(anchor='w')

        return {'valor': valor}

    def _build_tables(self) -> None:
        body = tk.Frame(self, bg=self.CONTENT_BG)
        body.pack(fill='both', expand=True, padx=28, pady=(0, 24))
        body.grid_columnconfigure(0, weight=3, uniform='tables')
        body.grid_columnconfigure(1, weight=2, uniform='tables')
        body.grid_rowconfigure(0, weight=1)

        mov_frame = self._create_table_container(body, 'Últimas movimentações')
        mov_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 8))

        columns_mov = ('data', 'produto', 'tipo', 'quantidade')
        self.tree_mov = ttk.Treeview(mov_frame, columns=columns_mov, show='headings', height=10)
        self.tree_mov.heading('data', text='Data')
        self.tree_mov.heading('produto', text='Produto')
        self.tree_mov.heading('tipo', text='Tipo')
        self.tree_mov.heading('quantidade', text='Qtd.')
        self.tree_mov.column('data', width=130, anchor='w')
        self.tree_mov.column('produto', width=220, anchor='w')
        self.tree_mov.column('tipo', width=80, anchor='center')
        self.tree_mov.column('quantidade', width=60, anchor='center')
        self.tree_mov.tag_configure('ENTRADA', foreground=self.SUCCESS)
        self.tree_mov.tag_configure('SAIDA', foreground='#dc2626')

        scroll_mov = ttk.Scrollbar(mov_frame, orient='vertical', command=self.tree_mov.yview)
        self.tree_mov.configure(yscrollcommand=scroll_mov.set)
        self.tree_mov.pack(side='left', fill='both', expand=True, padx=(12, 0), pady=(0, 12))
        scroll_mov.pack(side='right', fill='y', padx=(0, 12), pady=(0, 12))

        rep_frame = self._create_table_container(body, 'Produtos que precisam de reposição')
        rep_frame.grid(row=0, column=1, sticky='nsew')

        columns_rep = ('produto', 'quantidade', 'minimo')
        self.tree_rep = ttk.Treeview(rep_frame, columns=columns_rep, show='headings', height=10)
        self.tree_rep.heading('produto', text='Produto')
        self.tree_rep.heading('quantidade', text='Estoque')
        self.tree_rep.heading('minimo', text='Mínimo')
        self.tree_rep.column('produto', width=180, anchor='w')
        self.tree_rep.column('quantidade', width=70, anchor='center')
        self.tree_rep.column('minimo', width=70, anchor='center')
        self.tree_rep.tag_configure('zerado', foreground='#dc2626')

        scroll_rep = ttk.Scrollbar(rep_frame, orient='vertical', command=self.tree_rep.yview)
        self.tree_rep.configure(yscrollcommand=scroll_rep.set)
        self.tree_rep.pack(side='left', fill='both', expand=True, padx=(12, 0), pady=(0, 12))
        scroll_rep.pack(side='right', fill='y', padx=(0, 12), pady=(0, 12))

    def _create_table_container(self, master: tk.Frame, titulo: str) -> tk.Frame:
        container = tk.Frame(
            master,
            bg='white',
            highlightbackground='#e2e8f0',
            highlightthickness=1,
        )
        header = tk.Frame(container, bg='white')
        header.pack(fill='x', padx=12, pady=(12, 8))

        tk.Label(
            header,
            text=titulo,
            font=('Segoe UI', 11, 'bold'),
            bg='white',
            fg=self.TEXT_COLOR,
        ).pack(side='left')

        tk.Button(
            header,
            text='Atualizar',
            command=self.refresh,
            font=('Segoe UI', 9),
            bg=self.PRIMARY,
            fg='white',
            activebackground='#1d4ed8',
            activeforeground='white',
            bd=0,
            padx=12,
            pady=4,
            cursor='hand2',
        ).pack(side='right')

        return container

    def refresh(self) -> None:
        try:
            resumo = self.service.obter_resumo_dashboard()
            self.card_produtos['valor'].configure(text=str(resumo['produtos_ativos']))
            self.card_baixo['valor'].configure(text=str(resumo['estoque_baixo']))
            self.card_valor['valor'].configure(
                text=f"R$ {resumo['valor_estoque']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            )

            self.tree_mov.delete(*self.tree_mov.get_children())
            for mov in self.service.listar_ultimas_movimentacoes(limite=15):
                tipo = str(mov['tipo'])
                self.tree_mov.insert(
                    '',
                    'end',
                    values=(
                        str(mov['data_movimentacao']),
                        str(mov['produto_nome']),
                        'Entrada' if tipo == 'ENTRADA' else 'Saída',
                        int(mov['quantidade']),
                    ),
                    tags=(tipo,),
                )

            self.tree_rep.delete(*self.tree_rep.get_children())
            for produto in self.service.listar_produtos_reposicao():
                self.tree_rep.insert(
                    '',
                    'end',
                    values=(produto.nome, produto.quantidade, produto.quantidade_minima),
                    tags=('zerado',) if produto.quantidade == 0 else (),
                )
        except DatabaseError:
            pass
