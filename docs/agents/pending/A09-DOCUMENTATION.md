# A09 - Documentação Completa do Projeto

## 📋 Objetivo
Gerar documentação completa e navegável para a API (técnica e operacional) dentro de `docs/`, incluindo visão geral, setup, arquitetura, banco/migrations, autenticação, endpoints (OpenAPI), padrões de código e operações.

## 🎯 Tarefas
1. Configurar site de docs com MkDocs (tema Material)
2. Exportar OpenAPI estático da aplicação
3. Criar páginas: Visão Geral, Instalação, Arquitetura, Banco, Autenticação, Guia da API, Operação (Makefile), Padrões de Código
4. Integrar docstrings via mkdocstrings (Python) quando houver
5. Publicar local (serve) e gerar build estático

## 🔧 Comandos
```bash
# 0) Ativar venv
source .venv/bin/activate

# 1) Dependências de documentação
pip install mkdocs mkdocs-material mkdocstrings[python] pymdown-extensions

# 2) Exportar OpenAPI para docs/api/openapi.json
python scripts/export_openapi.py

# 3) Servir documentação local
mkdocs serve  # http://127.0.0.1:8000

# 4) Gerar build estático em site/
mkdocs build
```

## 🗂️ Arquivos a Criar

### mkdocs.yml
```yaml
author: i9 Smart
site_name: i9 Smart Campaigns API
site_url: http://localhost:8000/docs
repo_url: https://example.com/i9_smart_campaigns_api_fastapi
theme:
  name: material
  language: pt-BR
  features:
    - navigation.instant
    - content.code.copy
markdown_extensions:
  - admonition
  - pymdownx.highlight
  - pymdownx.superfences
  - toc:
      permalink: true
plugins:
  - search
  - mkdocstrings:
      default_handler: python
nav:
  - Visão Geral: index.md
  - Instalação & Uso: instalacao.md
  - Arquitetura: arquitetura.md
  - Banco & Migrations: banco.md
  - Autenticação: autenticacao.md
  - Guia da API (OpenAPI): guia-api.md
  - Operação (Makefile): operacao.md
  - Padrões de Código: estilo.md
```

### scripts/export_openapi.py
```python
from pathlib import Path
from fastapi.openapi.utils import get_openapi
from app.main import app

out = Path('docs/api')
out.mkdir(parents=True, exist_ok=True)
openapi = get_openapi(
    title=app.title,
    version=app.version,
    routes=app.routes,
)
(out / 'openapi.json').write_text(__import__('json').dumps(openapi, indent=2), encoding='utf-8')
print('✓ OpenAPI gerado em docs/api/openapi.json')
```

### docs/index.md
```markdown
# i9 Smart Campaigns API

Visão geral do projeto, contexto e principais recursos. Links rápidos para uso e endpoints.
```

### docs/instalacao.md
```markdown
# Instalação & Uso

- make install, make dev, make migrate
- Variáveis de ambiente (.env)
- Execução com Docker (docker-up)
```

### docs/arquitetura.md
```markdown
# Arquitetura

- Camadas: routes, services, models, config
- Fluxo de autenticação (JWT + API Key)
- Integrações: PostgreSQL, Redis, MinIO
```

### docs/banco.md
```markdown
# Banco & Migrations

- Alembic: comandos úteis (upgrade, revision)
- Tabelas principais: users, campaigns, campaign_images
- Enums: userrole, campaignstatus
```

### docs/autenticacao.md
```markdown
# Autenticação

- Login (JWT) e Refresh
- API Key para tablets (X-API-Key)
- Perfis: admin, editor, viewer
```

### docs/guia-api.md
```markdown
# Guia da API

- OpenAPI: `docs/api/openapi.json`
- Swagger/ReDoc em runtime: `/docs` e `/redoc`
- Exemplos com rest.http (tests/rest/rest.http)
```

### docs/operacao.md
```markdown
# Operação (Makefile)

- make dev, make run, make test, make migrate, make lint, make format, make type-check
- make docker-up/down, make security
```

### docs/estilo.md
```markdown
# Padrões de Código

- Black, Flake8, Mypy
- Convenções de nome: snake_case, PascalCase, UPPER_SNAKE_CASE
- Linhas até 120 colunas
```

## ✅ Checklist de Validação
- [ ] mkdocs.yml criado e validado
- [ ] OpenAPI exportado para docs/api/openapi.json
- [ ] Páginas base criadas e navegáveis
- [ ] mkdocs serve acessível localmente
- [ ] mkdocs build gera site/ sem erros

## 📊 Resultado Esperado
Documentação completa navegável em `mkdocs serve` e artefatos estáticos em `site/`, cobrindo visão geral, setup, arquitetura, banco de dados, autenticação, endpoints (OpenAPI), padrões e operação do projeto.
