# Arquitetura

- Framework: FastAPI (ASGI) em `app/`.
- Camadas:
  - `routes/`: endpoints REST, autenticação, tablets.
  - `services/`: regras de negócio (upload, cache, etc.).
  - `models/`: SQLAlchemy (users, campaigns, campaign_images).
  - `config/`: settings (.env) e database (engine, session).
- Integrações: PostgreSQL, Redis (cache), MinIO (storage S3).
