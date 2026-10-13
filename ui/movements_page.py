from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from database import DatabaseError
from models import Produto
from services import EstoqueService


class MovementsPage(tk.Frame):
    CONTENT_BG = '#f8fafc'
    TEXT_COLOR = '#0f172a'
    TEXT_MUTED = '#64748b'
    PRIMARY = '#2563eb'
    SUCCESS = '#16a34a'
    DANGER = '#dc2626'

    def __init__(self, master: tk.Misc, service: EstoqueService) -> None:
        super().__init__(master, bg=self.CONTENT_BG)
        self.service = service
        self.produtos: list[Produto] = []
        self.produtos_por_descricao: dict[str, Produto] = {}
        self.produtos_filtro_por_descricao: dict[str, Produto] = {}

        self._build_form()
        self._build_filters()
        self._build_table()
        self.carregar_produtos_ativos()
        self.carregar_movimentacoes()

    def _build_form(self) -> None:
        form = tk.Frame(
            self,
            bg='white',
            highlightbackground='#e2e8f0',
            highlightthickness=1,
            padx=18,
            pady=16,
        )
        form.pack(fill='x', padx=28, pady=(24, 12))

        for column in range(4):
            form.grid_columnconfigure(column, weight=1 if column in (1, 3) else 0)

        self.var_produto = tk.StringVar()
        self.var_tipo = tk.StringVar(value='ENTRADA')
        self.var_quantidade = tk.StringVar(value='1')
        self.var_observacao = tk.StringVar()

        self._add_label(form, 'Produto *', 0, 0)
        self.cmb_produto = ttk.Combobox(
            form,
            textvariable=self.var_produto,
            state='readonly',
            width=42,
        )
        self.cmb_produto.grid(row=0, column=1, sticky='ew', padx=(0, 16), pady=4)

        self._add_label(form, 'Tipo *', 0, 2)
        self.cmb_tipo = ttk.Combobox(
            form,
            textvariable=self.var_tipo,
            values=['ENTRADA', 'SAIDA'],
            state='readonly',
            width=12,
        )
        self.cmb_tipo.grid(row=0, column=3, sticky='w', pady=4)

        self._add_label(form, 'Quantidade *', 1, 0)
        self.entry_quantidade = self._add_entry(form, self.var_quantidade, 1, 1, width=12)

        self._add_label(form, 'Observação', 1, 2)
        self.entry_observacao = self._add_entry(form, self.var_observacao, 1, 3, width=32)

        buttons = tk.Frame(form, bg='white')
        buttons.grid(row=2, column=0, columnspan=4, sticky='w', pady=(14, 0))

        self._add_button(buttons, 'Registrar movimentação', self.registrar_movimentacao, self.PRIMARY).pack(side='left')
        self._add_button(buttons, 'Limpar', self.limpar_formulario, '#475569').pack(side='left', padx=(8, 0))
        self._add_button(buttons, 'Atualizar histórico', self.carregar_movimentacoes, '#0f766e').pack(side='left', padx=(8, 0))

    def _build_filters(self) -> None:
        filters = tk.Frame(
            self,
            bg='white',
            highlightbackground='#e2e8f0',
            highlightthickness=1,
            padx=18,
            pady=12,
        )
        filters.pack(fill='x', padx=28, pady=(0, 12))

        self.var_filtro_produto = tk.StringVar(value='Todos')
        self.var_filtro_tipo = tk.StringVar(value='Todos')
        self.var_data_inicio = tk.StringVar()
        self.var_data_fim = tk.StringVar()

        tk.Label(filters, text='Produto:', bg='white', fg=self.TEXT_COLOR).pack(side='left')
        self.cmb_filtro_produto = ttk.Combobox(
            filters,
            textvariable=self.var_filtro_produto,
            values=['Todos'],
            state='readonly',
            width=28,
        )
        self.cmb_filtro_produto.pack(side='left', padx=(8, 12))
        self.cmb_filtro_produto.bind('<<ComboboxSelected>>', lambda _event: self.carregar_movimentacoes())

        tk.Label(filters, text='Tipo:', bg='white', fg=self.TEXT_COLOR).pack(side='left')
        cmb_tipo = ttk.Combobox(
            filters,
            textvariable=self.var_filtro_tipo,
            values=['Todos', 'ENTRADA', 'SAIDA'],
            state='readonly',
            width=10,
        )
        cmb_tipo.pack(side='left', padx=(8, 12))
        cmb_tipo.bind('<<ComboboxSelected>>', lambda _event: self.carregar_movimentacoes())

        tk.Label(filters, text='De (AAAA-MM-DD):', bg='white', fg=self.TEXT_COLOR).pack(side='left')
        entry_inicio = tk.Entry(filters, textvariable=self.var_data_inicio, width=12)
        entry_inicio.pack(side='left', padx=(8, 12))
        entry_inicio.bind('<Return>', lambda _event: self.carregar_movimentacoes())

        tk.Label(filters, text='Até:', bg='white', fg=self.TEXT_COLOR).pack(side='left')
        entry_fim = tk.Entry(filters, textvariable=self.var_data_fim, width=12)
        entry_fim.pack(side='left', padx=(8, 12))
        entry_fim.bind('<Return>', lambda _event: self.carregar_movimentacoes())

        self._add_button(filters, 'Filtrar', self.carregar_movimentacoes, self.PRIMARY).pack(side='left')
        self._add_button(filters, 'Limpar filtros', self.limpar_filtros, '#475569').pack(side='left', padx=(8, 0))

    def _build_table(self) -> None:
        table_frame = tk.Frame(
            self,
            bg='white',
            highlightbackground='#e2e8f0',
            highlightthickness=1,
        )
        table_frame.pack(fill='both', expand=True, padx=28, pady=(0, 24))

        columns = ('id', 'data', 'produto', 'tipo', 'quantidade', 'observacao')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=12)
        headings = {
            'id': 'ID',
            'data': 'Data',
            'produto': 'Produto',
            'tipo': 'Tipo',
            'quantidade': 'Qtd.',
            'observacao': 'Observação',
        }
        widths = {
            'id': 50,
            'data': 150,
            'produto': 240,
            'tipo': 90,
            'quantidade': 70,
            'observacao': 260,
        }
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor='center' if column in {'id', 'data', 'tipo', 'quantidade'} else 'w')

        self.tree.tag_configure('entrada', foreground=self.SUCCESS)
        self.tree.tag_configure('saida', foreground=self.DANGER)

        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def _add_label(self, master: tk.Misc, text: str, row: int, column: int) -> None:
        tk.Label(master, text=text, bg='white', fg=self.TEXT_COLOR).grid(
            row=row,
            column=column,
            sticky='w',
            padx=(0, 8),
            pady=4,
        )

    def _add_entry(
        self,
        master: tk.Misc,
        variable: tk.StringVar,
        row: int,
        column: int,
        width: int,
    ) -> tk.Entry:
        entry = tk.Entry(master, textvariable=variable, width=width)
        entry.grid(row=row, column=column, sticky='ew', padx=(0, 16), pady=4)
        return entry

    def _add_button(self, master: tk.Misc, text: str, command, color: str) -> tk.Button:
        return tk.Button(
            master,
            text=text,
            command=command,
            bg=color,
            fg='white',
            activebackground=color,
            activeforeground='white',
            bd=0,
            padx=14,
            pady=7,
            cursor='hand2',
        )

    def carregar_produtos_ativos(self) -> None:
        try:
            self.produtos = self.service.listar_produtos(situacao='ATIVOS')
            produtos_filtro = self.service.listar_produtos(situacao='TODOS')
        except DatabaseError as exc:
            messagebox.showerror('Erro', str(exc), parent=self)
            return

        self.produtos_por_descricao = {
            f'{produto.id} - {produto.nome}': produto
            for produto in self.produtos
            if produto.id is not None
        }
        self.produtos_filtro_por_descricao = {
            f'{produto.id} - {produto.nome}': produto
            for produto in produtos_filtro
            if produto.id is not None
        }
        valores = list(self.produtos_por_descricao.keys())
        valores_filtro = list(self.produtos_filtro_por_descricao.keys())
        self.cmb_produto.configure(values=valores)
        self.cmb_filtro_produto.configure(values=['Todos', *valores_filtro])

        if valores and self.var_produto.get() not in valores:
            self.var_produto.set(valores[0])
        if self.var_filtro_produto.get() not in ['Todos', *valores_filtro]:
            self.var_filtro_produto.set('Todos')

    def carregar_movimentacoes(self) -> None:
        produto_id = self._produto_id_selecionado(
            self.var_filtro_produto.get(),
            self.produtos_filtro_por_descricao,
        )
        tipo = self.var_filtro_tipo.get().upper()
        tipo = tipo if tipo in {'ENTRADA', 'SAIDA'} else 'TODOS'

        data_inicio = self.var_data_inicio.get().strip()
        data_fim = self.var_data_fim.get().strip()
        if data_inicio and not self._data_valida(data_inicio):
            messagebox.showerror('Erro', 'Informe a data inicial no formato AAAA-MM-DD.', parent=self)
            return
        if data_fim and not self._data_valida(data_fim):
            messagebox.showerror('Erro', 'Informe a data final no formato AAAA-MM-DD.', parent=self)
            return

        try:
            movimentacoes = self.service.listar_movimentacoes(
                produto_id=produto_id,
                tipo=tipo,
                data_inicio=data_inicio,
                data_fim=data_fim,
            )
        except DatabaseError as exc:
            messagebox.showerror('Erro', str(exc), parent=self)
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        for movimentacao in movimentacoes:
            produto = self.service.obter_produto(movimentacao.produto_id)
            nome_produto = produto.nome if produto else f'Produto {movimentacao.produto_id}'
            tag = 'entrada' if movimentacao.tipo == 'ENTRADA' else 'saida'
            self.tree.insert(
                '',
                'end',
                values=(
                    movimentacao.id,
                    movimentacao.data_movimentacao or '',
                    nome_produto,
                    movimentacao.tipo,
                    movimentacao.quantidade,
                    movimentacao.observacao,
                ),
                tags=(tag,),
            )

    def registrar_movimentacao(self) -> None:
        produto_id = self._produto_id_selecionado(
            self.var_produto.get(),
            self.produtos_por_descricao,
        )
        if produto_id is None:
            messagebox.showwarning('Atenção', 'Selecione um produto cadastrado.', parent=self)
            return

        try:
            quantidade = int(self.var_quantidade.get().strip())
        except ValueError:
            messagebox.showerror('Erro', 'A quantidade deve ser um número inteiro.', parent=self)
            return

        try:
            movimentacao_id = self.service.registrar_movimentacao(
                produto_id=produto_id,
                tipo=self.var_tipo.get(),
                quantidade=quantidade,
                observacao=self.var_observacao.get(),
            )
        except (ValueError, DatabaseError) as exc:
            messagebox.showerror('Erro', str(exc), parent=self)
            return

        messagebox.showinfo('Sucesso', f'Movimentação {movimentacao_id} registrada com sucesso.', parent=self)
        self.limpar_formulario(manter_produto=True)
        self.carregar_produtos_ativos()
        self.carregar_movimentacoes()

    def limpar_formulario(self, manter_produto: bool = False) -> None:
        if not manter_produto:
            valores = self.cmb_produto.cget('values')
            self.var_produto.set(valores[0] if valores else '')
        self.var_tipo.set('ENTRADA')
        self.var_quantidade.set('1')
        self.var_observacao.set('')

    def limpar_filtros(self) -> None:
        self.var_filtro_produto.set('Todos')
        self.var_filtro_tipo.set('Todos')
        self.var_data_inicio.set('')
        self.var_data_fim.set('')
        self.carregar_movimentacoes()

    def _produto_id_selecionado(
        self,
        descricao: str,
        produtos: dict[str, Produto],
    ) -> int | None:
        if not descricao or descricao == 'Todos':
            return None
        produto = produtos.get(descricao)
        return produto.id if produto else None

    def _data_valida(self, value: str) -> bool:
        partes = value.split('-')
        if len(partes) != 3:
            return False
        ano, mes, dia = partes
        return (
            len(ano) == 4
            and len(mes) == 2
            and len(dia) == 2
            and ano.isdigit()
            and mes.isdigit()
            and dia.isdigit()
        )
