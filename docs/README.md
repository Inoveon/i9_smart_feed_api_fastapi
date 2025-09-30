# Documentação do Projeto

Este diretório contém a documentação do i9 Smart Campaigns API (MkDocs + Material).

- Homepage: `index.md`
- Seções: `installation.md`, `architecture.md`, `database.md`, `authentication.md`, `api-guide.md`, `operations.md`, `code-style.md`
- OpenAPI estático: `docs/api/openapi.json` (gerado por `scripts/export_openapi.py`)

## Como rodar
- Instalar deps (após ativar venv):
  - `pip install mkdocs mkdocs-material "mkdocstrings[python]" pymdown-extensions`
- Servir local: `mkdocs serve -a 127.0.0.1:8001`
- Gerar build: `mkdocs build` (saída em `site/`)

## Atualizar OpenAPI
- `python scripts/export_openapi.py`
