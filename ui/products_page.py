from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from database import DatabaseError
from models import Produto
from services import EstoqueService


class ProductsPage(tk.Frame):
    CONTENT_BG = '#f8fafc'
    TEXT_COLOR = '#0f172a'
    TEXT_MUTED = '#64748b'
    PRIMARY = '#2563eb'
    DANGER = '#dc2626'
    SUCCESS = '#16a34a'

    def __init__(self, master: tk.Misc, service: EstoqueService) -> None:
        super().__init__(master, bg=self.CONTENT_BG)
        self.service = service
        self.selected_id: int | None = None

        self._build_form()
        self._build_filters()
        self._build_table()
        self.carregar_categorias()
        self.limpar_formulario()
        self.carregar_produtos()

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

        self.var_nome = tk.StringVar()
        self.var_categoria = tk.StringVar()
        self.var_quantidade = tk.StringVar(value='0')
        self.var_minimo = tk.StringVar(value='0')
        self.var_custo = tk.StringVar(value='0.00')
        self.var_venda = tk.StringVar(value='0.00')
        self.var_situacao = tk.StringVar(value='Ativo')

        self._add_label(form, 'Nome *', 0, 0)
        self.entry_nome = self._add_entry(form, self.var_nome, 0, 1, width=32)

        self._add_label(form, 'Categoria', 1, 0)
        self.cmb_categoria = ttk.Combobox(
            form,
            textvariable=self.var_categoria,
            values=[],
            width=28,
        )
        self.cmb_categoria.grid(row=1, column=1, sticky='ew', padx=(0, 16), pady=4)

        self._add_label(form, 'Quantidade inicial', 1, 2)
        self.entry_quantidade = self._add_entry(form, self.var_quantidade, 1, 3, width=12)

        self._add_label(form, 'Estoque mínimo', 2, 0)
        self.entry_minimo = self._add_entry(form, self.var_minimo, 2, 1, width=12)

        self._add_label(form, 'Preço de custo', 2, 2)
        self.entry_custo = self._add_entry(form, self.var_custo, 2, 3, width=12)

        self._add_label(form, 'Preço de venda', 3, 0)
        self.entry_venda = self._add_entry(form, self.var_venda, 3, 1, width=12)

        self._add_label(form, 'Situação', 3, 2)
        self.cmb_situacao = ttk.Combobox(
            form,
            textvariable=self.var_situacao,
            values=['Ativo', 'Inativo'],
            state='disabled',
            width=10,
        )
        self.cmb_situacao.grid(row=3, column=3, sticky='w', pady=4)

        buttons = tk.Frame(form, bg='white')
        buttons.grid(row=4, column=0, columnspan=4, sticky='w', pady=(14, 0))

        self.btn_salvar = self._add_button(buttons, 'Cadastrar', self.salvar_produto, self.PRIMARY)
        self.btn_salvar.pack(side='left')

        self._add_button(buttons, 'Novo / Limpar', self.limpar_formulario, '#475569').pack(side='left', padx=(8, 0))
        self.btn_desativar = self._add_button(buttons, 'Desativar', self.alterar_situacao, self.DANGER)
        self.btn_desativar.pack(side='left', padx=(8, 0))
        self._add_button(buttons, 'Atualizar lista', self.carregar_produtos, '#0f766e').pack(side='left', padx=(8, 0))

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

        self.var_pesquisa = tk.StringVar()
        self.var_filtro_categoria = tk.StringVar(value='Todas')
        self.var_filtro_situacao = tk.StringVar(value='Ativos')

        tk.Label(filters, text='Pesquisar por nome ou código:', bg='white', fg=self.TEXT_COLOR).pack(side='left')
        entry_pesquisa = tk.Entry(filters, textvariable=self.var_pesquisa, width=28)
        entry_pesquisa.pack(side='left', padx=(8, 12))
        entry_pesquisa.bind('<Return>', lambda _event: self.carregar_produtos())

        tk.Label(filters, text='Categoria:', bg='white', fg=self.TEXT_COLOR).pack(side='left')
        self.cmb_filtro_categoria = ttk.Combobox(
            filters,
            textvariable=self.var_filtro_categoria,
            values=['Todas'],
            state='readonly',
            width=20,
        )
        self.cmb_filtro_categoria.pack(side='left', padx=(8, 12))
        self.cmb_filtro_categoria.bind('<<ComboboxSelected>>', lambda _event: self.carregar_produtos())

        tk.Label(filters, text='Situação:', bg='white', fg=self.TEXT_COLOR).pack(side='left')
        cmb_situacao = ttk.Combobox(
            filters,
            textvariable=self.var_filtro_situacao,
            values=['Ativos', 'Inativos', 'Todos'],
            state='readonly',
            width=10,
        )
        cmb_situacao.pack(side='left', padx=(8, 12))
        cmb_situacao.bind('<<ComboboxSelected>>', lambda _event: self.carregar_produtos())

        self._add_button(filters, 'Buscar', self.carregar_produtos, self.PRIMARY).pack(side='left')
        self._add_button(filters, 'Limpar filtros', self.limpar_filtros, '#475569').pack(side='left', padx=(8, 0))

    def _build_table(self) -> None:
        table_frame = tk.Frame(
            self,
            bg='white',
            highlightbackground='#e2e8f0',
            highlightthickness=1,
        )
        table_frame.pack(fill='both', expand=True, padx=28, pady=(0, 24))

        columns = (
            'id',
            'nome',
            'categoria',
            'quantidade',
            'minimo',
            'custo',
            'venda',
            'situacao',
            'data',
        )
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=12)
        headings = {
            'id': 'ID',
            'nome': 'Nome',
            'categoria': 'Categoria',
            'quantidade': 'Qtd.',
            'minimo': 'Estoque mín.',
            'custo': 'Preço custo',
            'venda': 'Preço venda',
            'situacao': 'Situação',
            'data': 'Data cadastro',
        }
        widths = {
            'id': 50,
            'nome': 220,
            'categoria': 140,
            'quantidade': 70,
            'minimo': 100,
            'custo': 100,
            'venda': 100,
            'situacao': 80,
            'data': 150,
        }
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor='center' if column != 'nome' else 'w')

        self.tree.tag_configure('inativo', foreground='#b91c1c')
        self.tree.tag_configure('baixo', background='#fef3c7')

        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.tree.bind('<<TreeviewSelect>>', self._on_select)

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

    def _add_button(
        self,
        master: tk.Misc,
        text: str,
        command,
        color: str,
    ) -> tk.Button:
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

    def carregar_categorias(self) -> None:
        try:
            categorias = self.service.listar_categorias()
        except DatabaseError as exc:
            messagebox.showerror('Erro', str(exc), parent=self)
            return

        self.cmb_categoria.configure(values=categorias)
        self.cmb_filtro_categoria.configure(values=['Todas', *categorias])
        if self.var_filtro_categoria.get() not in ['Todas', *categorias]:
            self.var_filtro_categoria.set('Todas')

    def carregar_produtos(self) -> None:
        situacao_map = {
            'Ativos': 'ATIVOS',
            'Inativos': 'INATIVOS',
            'Todos': 'TODOS',
        }
        try:
            produtos = self.service.listar_produtos(
                termo=self.var_pesquisa.get().strip(),
                categoria=self.var_filtro_categoria.get(),
                situacao=situacao_map.get(self.var_filtro_situacao.get(), 'ATIVOS'),
            )
        except DatabaseError as exc:
            messagebox.showerror('Erro', str(exc), parent=self)
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        for produto in produtos:
            tags = []
            if not produto.ativo:
                tags.append('inativo')
            if produto.quantidade < produto.quantidade_minima:
                tags.append('baixo')

            self.tree.insert(
                '',
                'end',
                iid=str(produto.id),
                values=(
                    produto.id,
                    produto.nome,
                    produto.categoria,
                    produto.quantidade,
                    produto.quantidade_minima,
                    self._formatar_moeda(produto.preco_custo),
                    self._formatar_moeda(produto.preco_venda),
                    'Ativo' if produto.ativo else 'Inativo',
                    produto.data_cadastro or '',
                ),
                tags=tags,
            )

    def limpar_filtros(self) -> None:
        self.var_pesquisa.set('')
        self.var_filtro_categoria.set('Todas')
        self.var_filtro_situacao.set('Ativos')
        self.carregar_produtos()

    def limpar_formulario(self) -> None:
        self.selected_id = None
        self.var_nome.set('')
        self.var_categoria.set('')
        self.var_quantidade.set('0')
        self.var_minimo.set('0')
        self.var_custo.set('0.00')
        self.var_venda.set('0.00')
        self.var_situacao.set('Ativo')
        self.entry_quantidade.configure(state='normal')
        self.cmb_situacao.configure(state='disabled')
        self.btn_salvar.configure(text='Cadastrar')
        self.btn_desativar.configure(text='Desativar')
        self.tree.selection_remove(self.tree.selection())

    def salvar_produto(self) -> None:
        try:
            produto = self._montar_produto()
            if self.selected_id is None:
                produto_id = self.service.cadastrar_produto(produto)
                messagebox.showinfo('Sucesso', f'Produto cadastrado com o código {produto_id}.', parent=self)
            else:
                self.service.atualizar_produto(produto)
                messagebox.showinfo('Sucesso', 'Produto atualizado com sucesso.', parent=self)
        except (ValueError, DatabaseError) as exc:
            messagebox.showerror('Erro', str(exc), parent=self)
            return

        self.carregar_categorias()
        self.limpar_formulario()
        self.carregar_produtos()

    def alterar_situacao(self) -> None:
        if self.selected_id is None:
            messagebox.showwarning('Atenção', 'Selecione um produto na tabela.', parent=self)
            return

        produto = self.service.obter_produto(self.selected_id)
        if produto is None:
            messagebox.showerror('Erro', 'Produto não encontrado.', parent=self)
            return

        if produto.ativo:
            if not messagebox.askyesno('Confirmar', 'Deseja desativar este produto?', parent=self):
                return
            self.service.desativar_produto(produto.id or 0)
            messagebox.showinfo('Sucesso', 'Produto desativado com sucesso.', parent=self)
        else:
            if not messagebox.askyesno('Confirmar', 'Deseja reativar este produto?', parent=self):
                return
            self.service.reativar_produto(produto.id or 0)
            messagebox.showinfo('Sucesso', 'Produto reativado com sucesso.', parent=self)

        self.limpar_formulario()
        self.carregar_produtos()

    def _montar_produto(self) -> Produto:
        quantidade = self._parse_int(self.var_quantidade.get(), 'Quantidade inicial')
        if self.selected_id is not None:
            atual = self.service.obter_produto(self.selected_id)
            quantidade = atual.quantidade if atual else 0

        return Produto(
            id=self.selected_id,
            nome=self.var_nome.get().strip(),
            categoria=self.var_categoria.get().strip(),
            quantidade=quantidade,
            quantidade_minima=self._parse_int(self.var_minimo.get(), 'Estoque mínimo'),
            preco_custo=self._parse_float(self.var_custo.get(), 'Preço de custo'),
            preco_venda=self._parse_float(self.var_venda.get(), 'Preço de venda'),
            ativo=self.var_situacao.get() == 'Ativo',
        )

    def _on_select(self, _event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            return

        produto = self.service.obter_produto(int(selection[0]))
        if produto is None:
            return

        self.selected_id = produto.id
        self.var_nome.set(produto.nome)
        self.var_categoria.set(produto.categoria)
        self.var_quantidade.set(str(produto.quantidade))
        self.var_minimo.set(str(produto.quantidade_minima))
        self.var_custo.set(f'{produto.preco_custo:.2f}')
        self.var_venda.set(f'{produto.preco_venda:.2f}')
        self.var_situacao.set('Ativo' if produto.ativo else 'Inativo')

        self.entry_quantidade.configure(state='disabled')
        self.cmb_situacao.configure(state='readonly')
        self.btn_salvar.configure(text='Salvar alterações')
        self.btn_desativar.configure(text='Desativar' if produto.ativo else 'Reativar')

    def _parse_int(self, value: str, field: str) -> int:
        try:
            return int(value.strip())
        except ValueError as exc:
            raise ValueError(f'{field} deve ser um número inteiro.') from exc

    def _parse_float(self, value: str, field: str) -> float:
        text = value.strip().replace('R$', '').strip()
        if ',' in text:
            text = text.replace('.', '').replace(',', '.')
        try:
            return float(text)
        except ValueError as exc:
            raise ValueError(f'{field} deve ser um número válido.') from exc

    def _formatar_moeda(self, value: float) -> str:
        return f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
