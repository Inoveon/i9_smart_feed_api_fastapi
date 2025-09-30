# Operação (Makefile)

Principais alvos:
- `make dev` – servidor com reload
- `make run` – servidor produção (sem reload)
- `make test` / `make test-cov` – testes (+ coverage)
- `make migrate` / `make migrate-create` – migrations Alembic
- `make lint`, `make format`, `make type-check`, `make security` – qualidade
- `make docker-up` / `make docker-down` – serviços Docker
