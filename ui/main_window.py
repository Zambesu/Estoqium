from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from reports import ReportService
from services import EstoqueService

from .dashboard_page import DashboardPage
from .movements_page import MovementsPage
from .products_page import ProductsPage
from .reports_page import ReportsPage


class MainWindow(tk.Tk):
    SIDEBAR_BG = '#0f172a'
    SIDEBAR_HOVER = '#1e293b'
    SIDEBAR_SELECTED = '#2563eb'
    CONTENT_BG = '#f8fafc'
    TEXT_COLOR = '#0f172a'
    TEXT_MUTED = '#64748b'

    def __init__(self, db_path: Path | str) -> None:
        super().__init__()
        self.db_path = Path(db_path)
        self.service = EstoqueService(self.db_path)
        self.report_service = ReportService(self.db_path)
        self.current_page = ''

        self.title('Estoqium')
        self.geometry('1120x720')
        self.minsize(920, 620)
        self.configure(bg=self.CONTENT_BG)

        self._configure_ttk()
        self._build_layout()
        self.show_page('Dashboard')

    def _configure_ttk(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass

        style.configure('TFrame', background=self.CONTENT_BG)
        style.configure('TLabel', background=self.CONTENT_BG, foreground=self.TEXT_COLOR)

    def _build_layout(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = tk.Frame(self, bg=self.SIDEBAR_BG, width=240)
        self.sidebar.grid(row=0, column=0, sticky='nsew')
        self.sidebar.grid_propagate(False)

        self.content = tk.Frame(self, bg=self.CONTENT_BG)
        self.content.grid(row=0, column=1, sticky='nsew')
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self._build_sidebar()
        self._build_pages()

        status = tk.Label(
            self,
            text=f'Banco de dados local: {self.db_path}',
            anchor='w',
            bg='#e2e8f0',
            fg='#475569',
            padx=12,
            pady=7,
        )
        status.grid(row=1, column=0, columnspan=2, sticky='ew')

    def _build_sidebar(self) -> None:
        brand = tk.Frame(self.sidebar, bg=self.SIDEBAR_BG)
        brand.pack(fill='x', padx=20, pady=(24, 18))

        tk.Label(
            brand,
            text='Estoqium',
            font=('Segoe UI', 18, 'bold'),
            bg=self.SIDEBAR_BG,
            fg='white',
        ).pack(anchor='w')

        tk.Label(
            brand,
            text='Controle de estoque local',
            font=('Segoe UI', 9),
            bg=self.SIDEBAR_BG,
            fg='#94a3b8',
        ).pack(anchor='w', pady=(2, 0))

        nav = tk.Frame(self.sidebar, bg=self.SIDEBAR_BG)
        nav.pack(fill='x', padx=10, pady=10)

        self.nav_buttons: dict[str, tk.Button] = {}
        for name in ['Dashboard', 'Produtos', 'Movimentações', 'Relatórios', 'Configurações']:
            button = tk.Button(
                nav,
                text=name,
                command=lambda page=name: self.show_page(page),
                font=('Segoe UI', 10),
                bg=self.SIDEBAR_BG,
                fg='#cbd5e1',
                activebackground=self.SIDEBAR_HOVER,
                activeforeground='white',
                bd=0,
                anchor='w',
                padx=18,
                pady=10,
                cursor='hand2',
                highlightthickness=0,
            )
            button.pack(fill='x', pady=2)
            button.bind('<Enter>', lambda _event, page=name: self._on_nav_hover(page, True))
            button.bind('<Leave>', lambda _event, page=name: self._on_nav_hover(page, False))
            self.nav_buttons[name] = button

    def _build_pages(self) -> None:
        descriptions = {
            'Dashboard': 'Visão geral do estoque e indicadores principais.',
            'Produtos': 'Cadastro, pesquisa e gerenciamento de produtos.',
            'Movimentações': 'Registro e histórico de entradas e saídas.',
            'Relatórios': 'Listagens, exportações e relatórios do estoque.',
            'Configurações': 'Preferências, backup e manutenção do sistema.',
        }

        self.pages: dict[str, tk.Frame] = {}
        for name, description in descriptions.items():
            page = tk.Frame(self.content, bg=self.CONTENT_BG)
            page.grid(row=0, column=0, sticky='nsew')

            header = tk.Frame(page, bg=self.CONTENT_BG)
            header.pack(fill='x', padx=28, pady=(28, 0))

            tk.Label(
                header,
                text=name,
                font=('Segoe UI', 20, 'bold'),
                bg=self.CONTENT_BG,
                fg=self.TEXT_COLOR,
            ).pack(anchor='w')

            tk.Label(
                header,
                text=description,
                font=('Segoe UI', 10),
                bg=self.CONTENT_BG,
                fg=self.TEXT_MUTED,
            ).pack(anchor='w', pady=(4, 0))

            if name == 'Dashboard':
                self.dashboard_page = DashboardPage(page, self.service)
                self.dashboard_page.pack(fill='both', expand=True)
            elif name == 'Produtos':
                ProductsPage(page, self.service).pack(fill='both', expand=True)
            elif name == 'Movimentações':
                MovementsPage(page, self.service).pack(fill='both', expand=True)
            elif name == 'Relatórios':
                ReportsPage(page, self.report_service).pack(fill='both', expand=True)
            else:
                card = tk.Frame(
                    page,
                    bg='white',
                    highlightbackground='#e2e8f0',
                    highlightthickness=1,
                )
                card.pack(fill='both', expand=True, padx=28, pady=24)

                tk.Label(
                    card,
                    text='Página em construção',
                    font=('Segoe UI', 14, 'bold'),
                    bg='white',
                    fg=self.TEXT_COLOR,
                ).pack(expand=True)

            self.pages[name] = page

    def _on_nav_hover(self, page: str, entering: bool) -> None:
        if page == self.current_page:
            return
        self.nav_buttons[page].configure(
            bg=self.SIDEBAR_HOVER if entering else self.SIDEBAR_BG
        )


        if page == 'Dashboard':
            self.dashboard_page.refresh()
    def show_page(self, page: str) -> None:
        self.current_page = page
        self.pages[page].tkraise()

        for name, button in self.nav_buttons.items():
            selected = name == page
            button.configure(
                bg=self.SIDEBAR_SELECTED if selected else self.SIDEBAR_BG,
                fg='white' if selected else '#cbd5e1',
            )
