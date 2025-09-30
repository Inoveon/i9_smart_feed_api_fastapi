# 📱 Padrões de Desenvolvimento FastAPI - i9 Smart Campaigns API

## 📅 Última Atualização: 2025-01-22
## 🤖 Documento de Referência para Desenvolvimento

## 📋 Visão Geral

Este documento estabelece os padrões de desenvolvimento FastAPI para o projeto i9 Smart Campaigns API.

## 🏗️ Arquitetura e Organização

### Estrutura de Diretórios
```
app/
├── config/                    # Configurações e settings
│   ├── database.py           # Configuração do banco
│   └── settings.py           # Pydantic Settings
├── models/                    # Modelos SQLAlchemy
│   ├── base.py               # Base e mixins
│   ├── campaign.py           # Modelo Campaign
│   └── image.py              # Modelo CampaignImage
├── schemas/                   # Pydantic schemas
│   ├── campaign.py           # Schemas de campanha
│   └── image.py              # Schemas de imagem
├── routes/                    # Endpoints/routers
│   ├── auth.py               # Autenticação
│   ├── campaigns.py          # CRUD campanhas
│   └── tablets.py            # Endpoints para tablets
├── services/                  # Lógica de negócio
│   ├── campaign_service.py   # Serviço de campanhas
│   └── image_service.py      # Serviço de imagens
├── dependencies/              # Dependências FastAPI
│   ├── auth.py               # Auth dependencies
│   └── cache.py              # Cache dependencies
├── middleware/                # Middlewares
│   └── api_key.py            # API Key validation
└── utils/                     # Utilitários
    └── storage.py             # MinIO/S3 utils
```

## 📚 1. Convenções de Nomenclatura

### 1.1 Arquivos e Módulos
```python
# Arquivos: snake_case.py
campaign_service.py
image_upload_handler.py

# Classes: PascalCase
class CampaignService:
class ImageProcessor:

# Funções: snake_case
def create_campaign():
def validate_image():

# Constantes: UPPER_SNAKE_CASE
MAX_UPLOAD_SIZE = 10485760
DEFAULT_DISPLAY_TIME = 5000
```

### 1.2 Rotas e Endpoints
```python
# RESTful naming
@router.get("/campaigns")          # Listar
@router.post("/campaigns")         # Criar
@router.get("/campaigns/{id}")     # Detalhe
@router.put("/campaigns/{id}")     # Atualizar
@router.delete("/campaigns/{id}")  # Deletar

# Ações customizadas com verbos
@router.post("/campaigns/{id}/activate")
@router.post("/campaigns/{id}/duplicate")
```

## 🎨 2. Pydantic Models

### 2.1 Schemas Organization
```python
# schemas/campaign.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

# Base schema com campos comuns
class CampaignBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    default_display_time: int = Field(default=5000, ge=1000, le=60000)

# Schema para criação
class CampaignCreate(CampaignBase):
    start_date: datetime
    end_date: datetime
    stations: List[str]
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date deve ser maior que start_date')
        return v

# Schema para resposta
class CampaignResponse(CampaignBase):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # SQLAlchemy compatibility
```

### 2.2 Validação Customizada
```python
from pydantic import validator, root_validator

class ImageUpload(BaseModel):
    filename: str
    content_type: str
    size_bytes: int
    
    @validator('content_type')
    def validate_content_type(cls, v):
        allowed = ['image/jpeg', 'image/png', 'image/webp']
        if v not in allowed:
            raise ValueError(f'Tipo não permitido. Use: {allowed}')
        return v
    
    @validator('size_bytes')
    def validate_size(cls, v):
        if v > 10 * 1024 * 1024:  # 10MB
            raise ValueError('Arquivo muito grande. Máximo: 10MB')
        return v
```

## 🔐 3. Autenticação e Segurança

### 3.1 JWT Implementation
```python
# dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.config.settings import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    return await UserService.get_by_email(email)

# Role-based access
def require_role(roles: List[str]):
    async def role_checker(current_user = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker
```

### 3.2 API Key para Tablets
```python
# middleware/api_key.py
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def validate_api_key(api_key: str = Security(api_key_header)):
    if not api_key or api_key != settings.API_KEY_TABLETS:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing API Key"
        )
    return api_key
```

## 🗄️ 4. Database Patterns

### 4.1 SQLAlchemy Models
```python
# models/campaign.py
from sqlalchemy import Column, String, DateTime, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin
import uuid

class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    status = Column(Enum(CampaignStatus), index=True)
    
    # Relationships
    images = relationship("CampaignImage", back_populates="campaign", cascade="all, delete-orphan")
```

### 4.2 Database Session
```python
# dependencies/database.py
from app.config.database import SessionLocal

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## 🎯 5. Service Layer Pattern

### 5.1 Service Structure
```python
# services/campaign_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.campaign import Campaign
from app.schemas.campaign import CampaignCreate, CampaignUpdate

class CampaignService:
    @staticmethod
    async def create_campaign(
        db: Session, 
        data: CampaignCreate, 
        user_id: str
    ) -> Campaign:
        campaign = Campaign(
            **data.dict(),
            created_by=user_id
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign
    
    @staticmethod
    async def get_active_campaigns(
        db: Session,
        station_id: str
    ) -> List[Campaign]:
        now = datetime.utcnow()
        return db.query(Campaign).filter(
            Campaign.status == "active",
            Campaign.start_date <= now,
            Campaign.end_date >= now,
            Campaign.stations.contains([station_id])
        ).all()
```

## 🚀 6. Async/Await Patterns

### 6.1 Async Endpoints
```python
@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Async file operations
    contents = await file.read()
    
    # Process asynchronously
    result = await process_upload(contents)
    
    return {"filename": file.filename, "result": result}
```

### 6.2 Background Tasks
```python
from fastapi import BackgroundTasks

@router.post("/campaigns/{id}/process")
async def process_campaign(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Add to background
    background_tasks.add_task(
        process_campaign_images,
        campaign_id
    )
    
    return {"message": "Processing started"}
```

## 🔄 7. Error Handling

### 7.1 Custom Exceptions
```python
# utils/exceptions.py
from fastapi import HTTPException

class CampaignNotFound(HTTPException):
    def __init__(self, campaign_id: str):
        super().__init__(
            status_code=404,
            detail=f"Campaign {campaign_id} not found"
        )

class InvalidDateRange(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=400,
            detail="End date must be after start date"
        )
```

### 7.2 Exception Handlers
```python
# main.py
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )
```

## 📝 8. Logging

### 8.1 Structured Logging
```python
import logging
from pythonjsonlogger import jsonlogger

# Configure logger
logger = logging.getLogger("campaigns_api")
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Use in code
logger.info("Campaign created", extra={
    "campaign_id": campaign.id,
    "user_id": user_id,
    "stations": campaign.stations
})
```

## 🧪 9. Testing Patterns

### 9.1 Pytest Fixtures
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers():
    # Get token
    token = "test_token"
    return {"Authorization": f"Bearer {token}"}
```

### 9.2 Test Structure
```python
# tests/test_campaigns.py
def test_create_campaign(client, auth_headers):
    response = client.post(
        "/api/campaigns",
        headers=auth_headers,
        json={
            "name": "Test Campaign",
            "start_date": "2025-01-01T00:00:00",
            "end_date": "2025-12-31T23:59:59"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Campaign"
```

## 🚀 10. Performance Optimization

### 10.1 Database Query Optimization
```python
# Use joinedload for relationships
from sqlalchemy.orm import joinedload

campaigns = db.query(Campaign)\
    .options(joinedload(Campaign.images))\
    .filter(Campaign.status == "active")\
    .all()
```

### 10.2 Caching
```python
# dependencies/cache.py
import redis
import json
from functools import wraps

redis_client = redis.from_url(settings.REDIS_URL)

def cache_result(expire: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            redis_client.setex(
                cache_key, 
                expire, 
                json.dumps(result, default=str)
            )
            
            return result
        return wrapper
    return decorator
```

## 📋 11. API Documentation

### 11.1 OpenAPI Customization
```python
# main.py
app = FastAPI(
    title="i9 Smart Campaigns API",
    description="API for managing advertising campaigns",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "campaigns",
            "description": "Campaign operations"
        },
        {
            "name": "images",
            "description": "Image management"
        }
    ]
)
```

### 11.2 Response Documentation
```python
@router.get(
    "/campaigns",
    response_model=List[CampaignResponse],
    summary="List all campaigns",
    description="Get a list of all campaigns with optional filters",
    responses={
        200: {"description": "Successful response"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized"}
    }
)
async def list_campaigns():
    pass
```

## ✅ 12. Checklist para Code Review

- [ ] Schemas Pydantic com validação apropriada
- [ ] Autenticação implementada corretamente
- [ ] Service layer separando lógica de negócio
- [ ] Tratamento de erros consistente
- [ ] Logs estruturados
- [ ] Testes para endpoints críticos
- [ ] Documentação OpenAPI completa
- [ ] Queries otimizadas
- [ ] Cache onde apropriado
- [ ] Sem secrets no código

---

**Última atualização**: 2025-01-22  
**Projeto**: i9 Smart Campaigns API  
**Framework**: FastAPI