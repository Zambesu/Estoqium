from __future__ import annotations

import os
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

from app_info import APP_NAME, APP_VERSION
from database import DatabaseError, backup_database, restore_database


class SettingsPage(tk.Frame):
    CONTENT_BG = '#f8fafc'
    TEXT_COLOR = '#0f172a'
    TEXT_MUTED = '#64748b'
    PRIMARY = '#2563eb'
    DANGER = '#dc2626'

    def __init__(self, master: tk.Misc, db_path: Path) -> None:
        super().__init__(master, bg=self.CONTENT_BG)
        self.db_path = Path(db_path)

        self._build_database_card()
        self._build_about_card()

    def _create_card(self, titulo: str) -> tk.Frame:
        card = tk.Frame(
            self,
            bg='white',
            highlightbackground='#e2e8f0',
            highlightthickness=1,
            padx=18,
            pady=16,
        )
        card.pack(fill='x', padx=28, pady=(24, 0))

        tk.Label(
            card,
            text=titulo,
            font=('Segoe UI', 12, 'bold'),
            bg='white',
            fg=self.TEXT_COLOR,
        ).pack(anchor='w', pady=(0, 10))
        return card

    def _build_database_card(self) -> None:
        card = self._create_card('Banco de dados')

        tk.Label(
            card,
            text='Local do arquivo de dados:',
            font=('Segoe UI', 9, 'bold'),
            bg='white',
            fg=self.TEXT_MUTED,
        ).pack(anchor='w')

        tk.Label(
            card,
            text=str(self.db_path),
            font=('Segoe UI', 10),
            bg='white',
            fg=self.TEXT_COLOR,
            wraplength=700,
            justify='left',
        ).pack(anchor='w', pady=(2, 12))

        buttons = tk.Frame(card, bg='white')
        buttons.pack(anchor='w')

        self._add_button(
            buttons, 'Abrir pasta de dados', self.abrir_pasta_dados, '#475569',
        ).pack(side='left')
        self._add_button(
            buttons, 'Criar backup...', self.criar_backup, self.PRIMARY,
        ).pack(side='left', padx=(8, 0))
        self._add_button(
            buttons, 'Restaurar backup...', self.restaurar_backup, self.DANGER,
        ).pack(side='left', padx=(8, 0))

        tk.Label(
            card,
            text=(
                'A restauração substitui todos os dados atuais pelos dados do backup. '
                'O arquivo é validado antes e o banco atual é preservado em caso de falha.'
            ),
            font=('Segoe UI', 8),
            bg='white',
            fg=self.TEXT_MUTED,
            wraplength=700,
            justify='left',
        ).pack(anchor='w', pady=(10, 0))

    def _build_about_card(self) -> None:
        card = self._create_card('Sobre o aplicativo')

        linhas = [
            f'{APP_NAME} — versão {APP_VERSION}',
            'Aplicativo 100% offline: nenhum dado sai do seu computador.',
            'Sem contas, sincronização, telemetria ou conexões de rede.',
            'Os dados ficam armazenados em um banco SQLite local na pasta de dados.',
        ]
        for linha in linhas:
            tk.Label(
                card,
                text=linha,
                font=('Segoe UI', 10),
                bg='white',
                fg=self.TEXT_COLOR,
                anchor='w',
                justify='left',
            ).pack(anchor='w', pady=1)

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

    def abrir_pasta_dados(self) -> None:
        pasta = self.db_path.parent
        pasta.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(pasta)  # type: ignore[attr-defined]
        except OSError as exc:
            messagebox.showerror(
                'Erro', f'Não foi possível abrir a pasta de dados:\n{exc}', parent=self,
            )

    def criar_backup(self) -> None:
        nome = f'estoqium_backup_{datetime.now():%Y%m%d_%H%M%S}.db'
        caminho = filedialog.asksaveasfilename(
            parent=self,
            title='Salvar backup do banco de dados',
            defaultextension='.db',
            initialfile=nome,
            filetypes=[('Banco de dados SQLite', '*.db'), ('Todos os arquivos', '*.*')],
            confirmoverwrite=True,
        )
        if not caminho:
            return

        try:
            destino = backup_database(caminho, self.db_path)
        except DatabaseError as exc:
            messagebox.showerror('Falha no backup', str(exc), parent=self)
            return

        messagebox.showinfo(
            'Backup concluído',
            f'Backup criado com sucesso em:\n{destino}',
            parent=self,
        )

    def restaurar_backup(self) -> None:
        caminho = filedialog.askopenfilename(
            parent=self,
            title='Selecionar arquivo de backup',
            filetypes=[('Banco de dados SQLite', '*.db'), ('Todos os arquivos', '*.*')],
        )
        if not caminho:
            return

        confirmar = messagebox.askyesno(
            'Confirmar restauração',
            'Esta ação substitui TODOS os dados atuais pelos dados do backup '
            'selecionado.\n\nDeseja continuar?',
            icon='warning',
            parent=self,
        )
        if not confirmar:
            return

        try:
            restore_database(caminho, self.db_path)
        except DatabaseError as exc:
            messagebox.showerror('Falha na restauração', str(exc), parent=self)
            return

        messagebox.showinfo(
            'Restauração concluída',
            'Backup restaurado com sucesso.\nReabra as telas para visualizar os dados.',
            parent=self,
        )
