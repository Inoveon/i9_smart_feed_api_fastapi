# Banco & Migrations

- Alembic configurado em `alembic.ini` e `migrations/`.
- Comandos:
  - `make migrate` – aplica até head
  - `make migrate-create name="mensagem"` – cria nova revisão com autogenerate
  - `make migrate-rollback` – desfaz última revisão
- Tabelas principais: `users`, `campaigns`, `campaign_images`.
- Enums: `userrole` (admin, editor, viewer), `campaignstatus` (active, scheduled, paused, expired).
