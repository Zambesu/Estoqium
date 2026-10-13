from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from database import DatabaseError
from reports import Report, ReportService


class ReportsPage(tk.Frame):
    CONTENT_BG = '#f8fafc'
    TEXT_COLOR = '#0f172a'
    TEXT_MUTED = '#64748b'
    PRIMARY = '#2563eb'
    SUCCESS = '#16a34a'

    RELATORIOS = {
        'Produtos ativos': 'ativos',
        'Estoque baixo': 'baixo',
        'Histórico de entradas e saídas': 'movimentacoes',
        'Valor estimado do estoque': 'valor',
    }

    def __init__(self, master: tk.Misc, report_service: ReportService) -> None:
        super().__init__(master, bg=self.CONTENT_BG)
        self.report_service = report_service
        self.report_atual: Report | None = None

        self._build_controls()
        self._build_table()
        self.gerar_relatorio()

    def _build_controls(self) -> None:
        controls = tk.Frame(
            self,
            bg='white',
            highlightbackground='#e2e8f0',
            highlightthickness=1,
            padx=18,
            pady=14,
        )
        controls.pack(fill='x', padx=28, pady=(24, 12))

        self.var_relatorio = tk.StringVar(value='Produtos ativos')
        self.var_data_inicio = tk.StringVar()
        self.var_data_fim = tk.StringVar()

        tk.Label(controls, text='Relatório:', bg='white', fg=self.TEXT_COLOR).pack(side='left')
        cmb = ttk.Combobox(
            controls,
            textvariable=self.var_relatorio,
            values=list(self.RELATORIOS.keys()),
            state='readonly',
            width=30,
        )
        cmb.pack(side='left', padx=(8, 16))
        cmb.bind('<<ComboboxSelected>>', lambda _event: self.gerar_relatorio())

        tk.Label(controls, text='De (AAAA-MM-DD):', bg='white', fg=self.TEXT_COLOR).pack(side='left')
        entry_inicio = tk.Entry(controls, textvariable=self.var_data_inicio, width=12)
        entry_inicio.pack(side='left', padx=(8, 8))
        entry_inicio.bind('<Return>', lambda _event: self.gerar_relatorio())

        tk.Label(controls, text='Até:', bg='white', fg=self.TEXT_COLOR).pack(side='left')
        entry_fim = tk.Entry(controls, textvariable=self.var_data_fim, width=12)
        entry_fim.pack(side='left', padx=(8, 16))
        entry_fim.bind('<Return>', lambda _event: self.gerar_relatorio())

        self._add_button(controls, 'Gerar', self.gerar_relatorio, self.PRIMARY).pack(side='left')
        self._add_button(
            controls, 'Exportar CSV', lambda: self.exportar('csv'), '#0f766e',
        ).pack(side='left', padx=(8, 0))
        self._add_button(
            controls, 'Exportar TXT', lambda: self.exportar('txt'), '#0f766e',
        ).pack(side='left', padx=(8, 0))

        hint = tk.Label(
            self,
            text='O filtro de período se aplica apenas ao histórico de entradas e saídas.',
            font=('Segoe UI', 8),
            bg=self.CONTENT_BG,
            fg=self.TEXT_MUTED,
            anchor='w',
        )
        hint.pack(fill='x', padx=28)

    def _build_table(self) -> None:
        container = tk.Frame(
            self,
            bg='white',
            highlightbackground='#e2e8f0',
            highlightthickness=1,
        )
        container.pack(fill='both', expand=True, padx=28, pady=(8, 24))

        self.lbl_titulo = tk.Label(
            container,
            text='',
            font=('Segoe UI', 11, 'bold'),
            bg='white',
            fg=self.TEXT_COLOR,
            anchor='w',
        )
        self.lbl_titulo.pack(fill='x', padx=12, pady=(12, 8))

        self.tree = ttk.Treeview(container, show='headings')
        scroll = ttk.Scrollbar(container, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side='left', fill='both', expand=True, padx=(12, 0), pady=(0, 12))
        scroll.pack(side='right', fill='y', padx=(0, 12), pady=(0, 12))

    def _add_button(self, master: tk.Frame, texto: str, comando, cor: str) -> tk.Button:
        return tk.Button(
            master,
            text=texto,
            command=comando,
            font=('Segoe UI', 9),
            bg=cor,
            fg='white',
            activebackground=cor,
            activeforeground='white',
            bd=0,
            padx=14,
            pady=6,
            cursor='hand2',
        )

    def gerar_relatorio(self) -> None:
        tipo = self.RELATORIOS[self.var_relatorio.get()]
        try:
            if tipo == 'ativos':
                self.report_atual = self.report_service.produtos_ativos()
            elif tipo == 'baixo':
                self.report_atual = self.report_service.estoque_baixo()
            elif tipo == 'movimentacoes':
                self.report_atual = self.report_service.movimentacoes(
                    self.var_data_inicio.get().strip(),
                    self.var_data_fim.get().strip(),
                )
            else:
                self.report_atual = self.report_service.valor_estoque()
        except DatabaseError as exc:
            messagebox.showerror('Erro ao gerar relatório', str(exc), parent=self)
            return

        titulo, headers, data = self.report_atual
        self.lbl_titulo.configure(text=f'{titulo} — {len(data)} registro(s)')

        self.tree.delete(*self.tree.get_children())
        self.tree.configure(columns=headers)
        for header in headers:
            self.tree.heading(header, text=header)
            self.tree.column(header, width=110, anchor='w')
        for row in data:
            self.tree.insert('', 'end', values=[str(valor) for valor in row])

    def exportar(self, formato: str) -> None:
        if self.report_atual is None:
            messagebox.showinfo('Exportação', 'Gere um relatório antes de exportar.', parent=self)
            return

        titulo = self.report_atual[0]
        nome_base = ''.join(c if c.isalnum() else '_' for c in titulo.lower()).strip('_')
        caminho = filedialog.asksaveasfilename(
            parent=self,
            title=f'Exportar {titulo}',
            defaultextension=f'.{formato}',
            initialfile=f'{nome_base}.{formato}',
            filetypes=[(f'Arquivo {formato.upper()}', f'*.{formato}')],
            confirmoverwrite=True,
        )
        if not caminho:
            return

        try:
            if formato == 'csv':
                path = self.report_service.exportar_csv(caminho, self.report_atual)
            else:
                path = self.report_service.exportar_txt(caminho, self.report_atual)
        except DatabaseError as exc:
            messagebox.showerror('Falha na exportação', str(exc), parent=self)
            return

        messagebox.showinfo(
            'Exportação concluída',
            f'Relatório exportado com sucesso para:\n{path}',
            parent=self,
        )
