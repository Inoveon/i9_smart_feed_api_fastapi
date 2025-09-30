# Diretrizes do Repositório

## Estrutura do Projeto e Módulos
- `app/` — Código FastAPI: `config/`, `models/`, `routes/`, `services/` (inclua `main.py` expondo `app`).
- `tests/` — Testes unitários e de integração (`tests/unit`, `tests/integration` opcionais).
- `migrations/` — Scripts do Alembic.
- `docs/` — Padrões e documentação (ver `docs/FASTAPI-STANDARDS.md`).
- `scripts/` — Scripts auxiliares e tarefas operacionais.
- Raiz — `Makefile`, `requirements*.txt`, `.env`.

## Comandos de Build, Teste e Desenvolvimento
- `make install` — Cria venv e instala dependências de `requirements.txt`.
- `make dev` — Sobe o servidor com reload (`uvicorn app.main:app`).
- `make run` — Servidor sem reload (ambiente mais próximo de prod).
- `make migrate` / `make migrate-create name="msg"` — Aplica ou cria migrations (Alembic).
- `make test` / `make test-cov` — Executa testes (coverage em `htmlcov/`).
- `make lint` / `make format` / `make type-check` — flake8, black, mypy.
- `make docker-up` / `make docker-down` — Sobe/derruba a stack local.

## Estilo de Código e Convenções
- Python 3, indentação de 4 espaços, largura máxima 120 colunas.
- Rode `make format` antes de commitar; usamos `black`, `flake8`, `mypy`.
- Nomes: módulos e funções em `snake_case`; classes em `PascalCase`; constantes em `UPPER_SNAKE_CASE`.
- Rotas em `app/routes/` por domínio; regras de negócio em `app/services/`.

## Diretrizes de Testes
- Framework: `pytest` (+ `pytest-asyncio`, `pytest-cov`).
- Testes em `tests/`; arquivos `test_*.py`; espelhe a estrutura do pacote.
- Tests rápidos e determinísticos; isole I/O; use fixtures para app/cliente.
- Execute: `make test` ou `make test-cov` (meta ≥ 80% quando viável).

## Commits e Pull Requests
- Use Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`.
- Commits focados; mantenha `make format` e `make lint` limpos.
- PRs devem incluir: resumo/objetivo, issue vinculada, passos de teste, capturas (ex.: `/docs`) e notas de migration.

## Segurança e Configuração
- Copie `.env.example` para `.env` (ou `make env-copy`); nunca versione segredos.
- Mudanças de banco exigem migration Alembic revisada.
- Centralize configs em `app/config/settings.py`; evite valores hardcoded.

## Visão de Arquitetura
- Entrypoint ASGI: `app/main.py` define `app` e inclui os routers.
- Prefira injeção de dependências, modelos Pydantic e camada de serviços.

## Instruções para Agentes
- Responda sempre em português (pt-BR) em issues, PRs, mensagens de commit e comentários de código, exceto quando um identificador/código exigir inglês.
