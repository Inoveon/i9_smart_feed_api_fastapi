# 🚀 i9 Smart Feed API

## 📋 Visão Geral

API centralizada para gerenciamento de feed de conteúdo do sistema i9 Smart Feed. Esta API fornece endpoints para criar, gerenciar e distribuir feeds com imagens para múltiplos postos/tablets.

## 🎯 Funcionalidades Principais

- ✅ CRUD completo de feeds
- ✅ Upload e gerenciamento de imagens
- ✅ Controle de tempo de exibição por imagem
- ✅ Agendamento de feeds (data início/fim)
- ✅ Ordenação de imagens drag-and-drop
- ✅ API Key para tablets (read-only)
- ✅ JWT para portal administrativo
- ✅ Cache inteligente com Redis
- ✅ Storage com MinIO/S3

## 🏗️ Arquitetura

```
FastAPI + PostgreSQL + Redis + MinIO
    ↓
Tablets (API Key) ← Feeds Ativos
    ↓
Portal Admin (JWT) → CRUD Completo
```

## 🔐 Autenticação

### Tablets (Read-Only)
- **Método**: API Key no header
- **Header**: `X-API-Key: i9smart_feed_readonly_2025`
- **Permissões**: Apenas leitura de feeds ativos

### Portal Admin
- **Método**: JWT Bearer Token
- **Login**: POST /api/auth/login
- **Roles**: admin, editor, viewer

## 📊 Modelos de Dados

### Feed
```python
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "status": "active|scheduled|paused|expired",
  "start_date": "datetime",
  "end_date": "datetime",
  "default_display_time": 5000,  # milliseconds
  "stations": ["station_id"],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### FeedImage
```python
{
  "id": "uuid",
  "feed_id": "uuid",
  "filename": "string",
  "url": "string",
  "order": 0,
  "display_time": 5000,  # override
  "title": "string",
  "active": true
}
```

## 🔗 Endpoints Principais

### Feeds
- `GET /api/feeds` - Listar feeds
- `GET /api/feeds/{id}` - Detalhes do feed
- `POST /api/feeds` - Criar feed
- `PUT /api/feeds/{id}` - Atualizar feed
- `DELETE /api/feeds/{id}` - Remover feed
- `GET /api/feeds/active/{station_id}` - Feeds ativos por posto

### Imagens
- `POST /api/feeds/{id}/images` - Upload de imagens
- `PUT /api/feeds/{id}/images/order` - Reordenar imagens
- `DELETE /api/images/{id}` - Remover imagem
- `PUT /api/images/{id}` - Atualizar propriedades da imagem

### Autenticação
- `POST /api/auth/login` - Login portal
- `POST /api/auth/refresh` - Renovar token
- `GET /api/auth/verify` - Verificar API Key

## 🛠️ Stack Tecnológica

- **Framework**: FastAPI 0.109+
- **Python**: 3.11+
- **Banco de Dados**: PostgreSQL 15
- **Cache**: Redis 7
- **Storage**: MinIO (S3-compatible)
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Validação**: Pydantic 2.0
- **Testes**: Pytest
- **Docs**: Swagger/ReDoc automático

## 🚀 Instalação

### Pré-requisitos
- Python 3.11+
- PostgreSQL 15
- Redis 7
- MinIO (ou S3)

### Setup Local

1. Clone o repositório
```bash
cd /Users/leechardes/Projetos/i9_smart/apis/
cd i9_smart_feed_api_fastapi
```

2. Crie ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
```

3. Instale dependências
```bash
pip install -r requirements.txt
```

4. Configure variáveis de ambiente
```bash
cp .env.example .env
# Edite .env com suas configurações
```

5. Execute migrations
```bash
alembic upgrade head
```

6. Inicie o servidor
```bash
uvicorn app.main:app --reload --port 8000
```

## 🐳 Docker

```bash
# Build
docker build -t i9-feed-api .

# Run com docker-compose
docker-compose up -d
```

## 📝 Documentação

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Docs técnicos**: `/docs/`

## 🧪 Testes

```bash
# Todos os testes
pytest

# Com coverage
pytest --cov=app

# Específico
pytest tests/test_feeds.py
```

## 📂 Estrutura do Projeto

```
i9_smart_feed_api_fastapi/
├── app/
│   ├── main.py              # Entry point
│   ├── config/              # Configurações
│   ├── models/              # Modelos SQLAlchemy
│   ├── routes/              # Endpoints
│   └── services/            # Lógica de negócio
├── tests/                   # Testes
├── migrations/              # Alembic migrations
├── docs/                    # Documentação
│   └── agents/             # Agentes de automação
└── scripts/                 # Scripts úteis
```

## 🤖 Agentes Disponíveis

- `A01-SETUP-ENVIRONMENT` - Configurar ambiente inicial
- `A02-DATABASE-SETUP` - Criar banco e migrations
- `A03-API-DEVELOPMENT` - Desenvolvimento de endpoints
- `A04-TESTING` - Implementar testes
- `A05-DEPLOYMENT` - Deploy e CI/CD

## 📞 Contato

**Projeto**: i9 Smart Feed
**Categoria**: i9_smart/apis
**Tecnologia**: FastAPI
**Status**: Em desenvolvimento

---

*Última atualização: 2025-01-22*