# Instalação & Uso

- Pré-requisitos: Python 3.11+, PostgreSQL, Redis, MinIO.
- Crie e ative a venv: `python -m venv .venv && source .venv/bin/activate`.
- Instale deps: `make install`.
- Configure `.env` (use `make env-copy` se houver `.env.example`).
- Migrações: `make migrate`.
- Rodar dev: `make dev` (ou `make run` para sem reload).
- Docker (opcional): `make docker-up` / `make docker-down`.
