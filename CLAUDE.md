# 🤖 Instruções para Claude - i9 Smart Feed API

## 📋 Contexto do Projeto

Você está trabalhando na API de feed de conteúdo do sistema i9 Smart Feed. Esta API gerencia feeds com imagens que são exibidas em tablets/totems em múltiplos postos.

## 🎯 Objetivo Principal

Criar uma API robusta e escalável para:
1. Gerenciar feeds de conteúdo
2. Upload e ordenação de imagens
3. Controle de tempo de exibição individual
4. Agendamento com data início/fim
5. Distribuição para múltiplos postos

## 🏗️ Arquitetura Definida

### Stack
- **Framework**: FastAPI 0.109+
- **Python**: 3.11+
- **Banco**: PostgreSQL 15
- **Cache**: Redis 7
- **Storage**: MinIO (S3-compatible)
- **ORM**: SQLAlchemy 2.0

### Autenticação
- **Tablets**: API Key simples (read-only)
- **Portal**: JWT com roles (admin/editor/viewer)

## 📊 Modelos de Dados

### Feed
```python
class Feed:
    id: UUID
    name: str
    description: Optional[str]
    status: Literal["active", "scheduled", "paused", "expired"]
    start_date: datetime
    end_date: datetime
    default_display_time: int  # milliseconds
    stations: List[str]  # IDs dos postos
    priority: int = 0
    created_by: UUID
    created_at: datetime
    updated_at: datetime
```

### FeedImage
```python
class FeedImage:
    id: UUID
    feed_id: UUID
    filename: str
    url: str
    order: int
    display_time: Optional[int]  # override do tempo padrão
    title: Optional[str]
    description: Optional[str]
    active: bool = True
    size_bytes: int
    mime_type: str
    uploaded_at: datetime
```

## 🔗 Endpoints Essenciais

### Para Tablets (API Key)
```
GET /api/feeds/active/{station_id}
- Retorna feeds ativos para o posto
- Inclui imagens ordenadas
- Cache de 5 minutos
```

### Para Portal (JWT)
```
# Feeds
GET    /api/feeds
POST   /api/feeds
GET    /api/feeds/{id}
PUT    /api/feeds/{id}
DELETE /api/feeds/{id}

# Imagens
POST   /api/feeds/{id}/images
PUT    /api/feeds/{id}/images/order
DELETE /api/images/{id}

# Analytics
GET    /api/feeds/{id}/stats
GET    /api/reports/feeds
```

## 🛠️ Padrões de Desenvolvimento

### Estrutura de Código
```python
# routes/feeds.py
@router.get("/feeds")
async def list_feeds(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista feeds com paginação e filtros."""
    pass

# services/feed_service.py
class FeedService:
    def create_feed(self, data: FeedCreate) -> Feed:
        """Lógica de negócio para criar feed."""
        pass
```

### Validações Importantes
1. Datas: `end_date` sempre maior que `start_date`
2. Imagens: Máximo 10MB, formatos: jpg, png, webp
3. Display time: Mínimo 1000ms, máximo 60000ms
4. Ordenação: Sempre sequencial sem gaps

### Tratamento de Erros
```python
class FeedNotFound(HTTPException):
    def __init__(self, feed_id: str):
        super().__init__(
            status_code=404,
            detail=f"Feed {feed_id} not found"
        )
```

## 🔐 Segurança

### Headers Obrigatórios
- CORS configurado para portal específico
- Rate limiting: 1000 req/min para API Key
- Helmet headers para segurança

### Validação de Entrada
- Sempre usar Pydantic models
- Sanitizar nomes de arquivo
- Validar mime types de imagens
- SQL injection prevention via ORM

## 📦 Dependências Principais

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9
redis==5.0.1
minio==7.2.3
pydantic==2.5.3
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pillow==10.2.0
pytest==7.4.4
pytest-asyncio==0.23.3
```

## 🧪 Testes Obrigatórios

### Unitários
- Services: 100% coverage
- Validações de modelo
- Autenticação e autorização

### Integração
- Endpoints com banco real
- Upload de imagens
- Cache Redis

### E2E
- Fluxo completo de feed
- API Key dos tablets
- Portal admin

## 🚀 Comandos Úteis

```bash
# Desenvolvimento
uvicorn app.main:app --reload --port 8000

# Migrations
alembic revision --autogenerate -m "descrição"
alembic upgrade head

# Testes
pytest -v
pytest --cov=app tests/

# Lint
black app/
flake8 app/
mypy app/
```

## 📝 TODOs Prioritários

1. [ ] Implementar modelos SQLAlchemy
2. [ ] Criar sistema de autenticação
3. [ ] Endpoints CRUD de feeds
4. [ ] Upload e processamento de imagens
5. [ ] Sistema de cache com Redis
6. [ ] Validação de períodos
7. [ ] Analytics básico
8. [ ] Documentação Swagger
9. [ ] Testes automatizados
10. [ ] Docker e CI/CD

## ⚠️ Avisos Importantes

- **Não commitar**: .env, uploads/, *.pyc
- **Sempre testar**: Upload de imagens antes de deploy
- **Cache**: Invalidar ao atualizar feed
- **Backup**: Imagens devem ter backup em S3

## 🎓 Referências

- [FastAPI Docs](https://fastapi.tiangolo.com)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org)
- [MinIO Python SDK](https://min.io/docs/minio/linux/developers/python/minio-py.html)
- [JWT Auth Tutorial](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)

---

**Projeto**: i9 Smart Feed API
**Última atualização**: 2025-01-22
**Status**: Pronto para desenvolvimento