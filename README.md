# Estoqium

Sistema desktop local para controle de estoque de pequenos comércios, desenvolvido em Python com Tkinter e SQLite. Interface em português brasileiro e funcionamento 100% offline — sem contas, sincronização, telemetria ou conexões de rede.

## Funcionalidades

### Dashboard

- Cartões com produtos ativos, produtos com estoque baixo e valor estimado do estoque (quantidade × preço de custo).
- Tabela com as últimas movimentações.
- Lista de produtos que precisam de reposição (quantidade menor ou igual ao estoque mínimo, incluindo zerados).
- Indicadores atualizados automaticamente ao voltar à página.

### Produtos

- Cadastro, edição, listagem e pesquisa por nome ou código.
- Filtro por categoria e situação (ativos/inativos).
- Desativação sem apagar o histórico, com possibilidade de reativação.
- Validação de campos obrigatórios e bloqueio de valores negativos.
- Quantidade inicial registrada como movimentação de entrada.

### Movimentações

- Registro de entradas e saídas com observação opcional.
- Histórico com filtro por produto, tipo e período.
- Atualização automática do estoque em transação SQLite.
- Bloqueio de saída maior que o estoque disponível e de movimentação em produto inativo.

### Relatórios

- Produtos ativos, estoque baixo, histórico de entradas/saídas (com filtro de período) e valor estimado do estoque.
- Pré-visualização em tabela antes de exportar.
- Exportação para CSV (UTF-8 com BOM, compatível com Excel) e TXT formatado, em pasta escolhida pelo usuário, com confirmação antes de sobrescrever.

### Configurações

- Exibição do caminho do banco de dados e abertura da pasta de dados.
- Backup do banco em local escolhido pelo usuário, usando a API de backup do SQLite (cópia consistente mesmo com o banco aberto).
- Restauração com validação de integridade do arquivo, confirmação explícita e preservação do banco atual em caso de falha.
- Versão do aplicativo e informações sobre o funcionamento offline.

## Requisitos

- Python 3.10 ou superior.
- Nenhuma dependência externa para executar o aplicativo (Tkinter e SQLite fazem parte da biblioteca padrão).
- `pytest` apenas para rodar os testes automatizados (desenvolvimento).

## Como executar

```bash
python main.py
```

Se estiver usando a `.venv` dentro do projeto:

```powershell
.\.venv\Scripts\python.exe main.py
```

O banco de dados será criado automaticamente em `data/estoque.db`.

## Testes

```bash
pip install pytest
python -m pytest tests -v
```

A suíte usa bancos temporários e não altera os dados reais. Cobre inicialização do banco, regras de produtos e movimentações, cálculos do Dashboard, relatórios, backup e restauração.

## Estrutura do projeto

```text
Estoqium/
├── main.py              # Inicialização da aplicação
├── app_info.py          # Nome e versão do aplicativo
├── database.py          # Conexão, schema, backup e restauração (SQLite)
├── models.py            # Dataclasses Produto e Movimentacao
├── services.py          # Regras de negócio de produtos e movimentações
├── reports.py           # Geração e exportação de relatórios (CSV/TXT)
├── requirements.txt
├── README.md
├── .gitignore
├── data/                # Banco de dados local (criado na 1ª execução)
├── tests/               # Testes automatizados com pytest
└── ui/
    ├── __init__.py
    ├── main_window.py   # Janela principal e menu lateral
    ├── dashboard_page.py
    ├── products_page.py
    ├── movements_page.py
    ├── reports_page.py
    └── settings_page.py
```

## Arquitetura

O projeto segue camadas separadas: a interface (`ui/`) não contém regras de negócio, que ficam em `services.py` e `reports.py`; o acesso ao banco fica em `database.py`; e os modelos em `models.py`.

## Observações

- O sistema funciona totalmente offline: nenhum dado sai do computador.
- Os dados ficam em um banco SQLite local na pasta `data/`.
- Todas as mensagens da interface estão em português brasileiro.
