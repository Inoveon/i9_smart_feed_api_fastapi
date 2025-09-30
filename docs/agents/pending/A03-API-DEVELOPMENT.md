# A03 - API Development

## 📋 Objetivo
Desenvolver todos os endpoints da API de campanhas, incluindo CRUD completo, upload de imagens, autenticação e autorização.

## 🎯 Tarefas

### 1. Sistema de Autenticação
- [ ] Implementar login com JWT
- [ ] Criar middleware de API Key para tablets
- [ ] Implementar refresh token
- [ ] Criar decoradores de permissão

### 2. Endpoints de Campanhas
- [ ] GET /api/campaigns - Listar campanhas
- [ ] POST /api/campaigns - Criar campanha
- [ ] GET /api/campaigns/{id} - Detalhes
- [ ] PUT /api/campaigns/{id} - Atualizar
- [ ] DELETE /api/campaigns/{id} - Soft delete
- [ ] GET /api/campaigns/active/{station_id} - Para tablets

### 3. Endpoints de Imagens
- [ ] POST /api/campaigns/{id}/images - Upload múltiplo
- [ ] PUT /api/campaigns/{id}/images/order - Reordenar
- [ ] DELETE /api/images/{id} - Remover imagem
- [ ] PUT /api/images/{id} - Atualizar propriedades

### 4. Sistema de Cache
- [ ] Configurar Redis client
- [ ] Cache para campanhas ativas
- [ ] Invalidação de cache
- [ ] TTL configurável

## 🔧 Implementação

### 1. Estrutura de Routers

```python
# app/routes/__init__.py
from fastapi import APIRouter
from app.routes import auth, campaigns, images, tablets

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
api_router.include_router(images.router, prefix="/images", tags=["images"])
api_router.include_router(tablets.router, prefix="/tablets", tags=["tablets"])
```

### 2. Autenticação JWT

```python
# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.config.settings import settings
from app.models.user import User
from app.schemas.auth import Token, TokenData
from app.services.auth_service import AuthService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = AuthService.create_access_token(
        data={"sub": user.email, "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return TokenData(email=email)
    except JWTError:
        raise credentials_exception
```

### 3. Middleware API Key

```python
# app/middleware/api_key.py
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config.settings import settings

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.API_KEY_TABLETS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    return api_key
```

### 4. Endpoints de Campanhas

```python
# app/routes/campaigns.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignResponse
from app.services.campaign_service import CampaignService
from app.dependencies.auth import require_role

router = APIRouter()

@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    station_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista campanhas com filtros e paginação."""
    return CampaignService.list_campaigns(db, skip, limit, status, station_id)

@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "editor"]))
):
    """Cria nova campanha."""
    return CampaignService.create_campaign(db, campaign, current_user.id)

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna detalhes da campanha."""
    campaign = CampaignService.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    campaign: CampaignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "editor"]))
):
    """Atualiza campanha existente."""
    return CampaignService.update_campaign(db, campaign_id, campaign)

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """Soft delete da campanha."""
    CampaignService.delete_campaign(db, campaign_id)
    return {"message": "Campaign deleted successfully"}
```

### 5. Endpoint para Tablets

```python
# app/routes/tablets.py
from fastapi import APIRouter, Depends
from app.middleware.api_key import verify_api_key
from app.services.campaign_service import CampaignService
from app.dependencies.cache import cache_key_wrapper

router = APIRouter()

@router.get("/campaigns/active/{station_id}")
@cache_key_wrapper(expire=300)  # Cache 5 minutos
async def get_active_campaigns(
    station_id: str,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Retorna campanhas ativas para o posto específico."""
    campaigns = CampaignService.get_active_campaigns_for_station(db, station_id)
    return {
        "station_id": station_id,
        "campaigns": campaigns,
        "timestamp": datetime.now().isoformat()
    }
```

### 6. Upload de Imagens

```python
# app/routes/images.py
from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import List
from app.services.image_service import ImageService

router = APIRouter()

@router.post("/campaigns/{campaign_id}/images")
async def upload_images(
    campaign_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "editor"]))
):
    """Upload múltiplo de imagens."""
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed")
    
    uploaded = []
    for file in files:
        # Validar tipo e tamanho
        if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
            raise HTTPException(status_code=400, detail=f"Invalid file type: {file.content_type}")
        
        image = await ImageService.upload_image(db, campaign_id, file)
        uploaded.append(image)
    
    return {"uploaded": len(uploaded), "images": uploaded}

@router.put("/campaigns/{campaign_id}/images/order")
async def reorder_images(
    campaign_id: str,
    order: List[str],  # Lista de IDs em nova ordem
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "editor"]))
):
    """Reordena imagens da campanha."""
    ImageService.reorder_images(db, campaign_id, order)
    return {"message": "Images reordered successfully"}
```

### 7. Cache com Redis

```python
# app/dependencies/cache.py
import redis
import json
from functools import wraps
from app.config.settings import settings

redis_client = redis.from_url(settings.REDIS_URL)

def cache_key_wrapper(expire=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Gerar chave do cache
            cache_key = f"{func.__name__}:{':'.join(map(str, args))}:{':'.join(f'{k}={v}' for k, v in kwargs.items())}"
            
            # Verificar cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Executar função
            result = await func(*args, **kwargs)
            
            # Salvar no cache
            redis_client.setex(cache_key, expire, json.dumps(result, default=str))
            
            return result
        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """Invalida cache por padrão."""
    for key in redis_client.scan_iter(match=pattern):
        redis_client.delete(key)
```

## ✅ Checklist de Validação

- [ ] Autenticação JWT funcionando
- [ ] API Key para tablets validada
- [ ] CRUD de campanhas completo
- [ ] Upload de imagens funcionando
- [ ] Reordenação de imagens OK
- [ ] Cache Redis implementado
- [ ] Documentação Swagger atualizada
- [ ] Validações de entrada
- [ ] Tratamento de erros
- [ ] Logs estruturados

## 📊 Resultado Esperado

API completa com:
- Todos os endpoints funcionando
- Autenticação e autorização
- Upload de imagens otimizado
- Cache para performance
- Documentação automática

Testar:
```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Tablet API Key
curl -X GET http://localhost:8000/api/tablets/campaigns/active/001 \
  -H "X-API-Key: i9smart_campaigns_readonly_2025"
```

---

*Próximo agente: A04-TESTING*