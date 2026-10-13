# Estoqium

Sistema desktop local para controle de estoque de pequenos comércios, desenvolvido em Python com Tkinter e SQLite.

## Status atual

Estrutura inicial do projeto com:

- Inicialização da aplicação.
- Criação automática do banco de dados SQLite na primeira execução.
- Janela principal em português brasileiro.
- Menu lateral com páginas vazias para Dashboard, Produtos, Movimentações, Relatórios e Configurações.

## Requisitos

- Python 3.10 ou superior.
- Nenhuma dependência externa nesta etapa.

## Como executar

```bash
python main.py
```

O banco de dados será criado automaticamente em `data/estoqium.db`.

## Estrutura do projeto

```text
Estoqium/
├── main.py
├── database.py
├── models.py
├── services.py
├── reports.py
├── requirements.txt
├── README.md
├── .gitignore
└── ui/
    ├── __init__.py
    └── main_window.py
```

## Observações

- O sistema funciona totalmente offline.
- Não utiliza APIs, servidores ou conexões de rede.
- As regras de movimentação, alertas, relatórios e configurações serão implementadas nas próximas etapas.
