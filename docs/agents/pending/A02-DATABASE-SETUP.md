# A02 - Database Setup

## 📋 Objetivo
Configurar o banco de dados PostgreSQL, criar modelos SQLAlchemy, implementar migrations com Alembic e popular dados iniciais.

## 🔐 Dados de Acesso ao Banco de Dados

```yaml
Host: 10.0.10.5
Port: 5432
Database: i9_campaigns
Username: campaigns_user
Password: Camp@2025#Secure
Connection String: postgresql://campaigns_user:Camp@2025#Secure@10.0.10.5:5432/i9_campaigns
```

**Nota**: O banco e usuário já foram criados e configurados com todas as permissões necessárias.

## 🎯 Tarefas

### 1. Configuração do Banco
- [x] Criar banco de dados no PostgreSQL ✅
- [x] Criar usuário dedicado com senha segura ✅
- [x] Configurar permissões do usuário ✅
- [ ] Testar conexão com o banco
- [ ] Configurar pool de conexões

### 2. Modelos SQLAlchemy
- [ ] Criar modelo Campaign
- [ ] Criar modelo CampaignImage
- [ ] Criar modelo User (para portal)
- [ ] Criar modelo AuditLog
- [ ] Definir relacionamentos

### 3. Alembic Setup
- [ ] Inicializar Alembic
- [ ] Criar primeira migration
- [ ] Aplicar migrations
- [ ] Criar script de seed

### 4. Índices e Otimizações
- [ ] Criar índices necessários
- [ ] Configurar constraints
- [ ] Adicionar triggers para updated_at

## 🔧 Comandos

```bash
# Ativar ambiente
cd /Users/leechardes/Projetos/i9_smart/apis/i9_smart_campaigns_api_fastapi
source .venv/bin/activate

# 1. Inicializar Alembic
alembic init migrations

# 2. Configurar alembic.ini com os dados de acesso reais
# DADOS DE ACESSO AO BANCO:
# Host: 10.0.10.5
# Port: 5432
# Database: i9_campaigns
# User: campaigns_user
# Password: Camp@2025#Secure
# 
# Editar: sqlalchemy.url = postgresql://campaigns_user:Camp@2025#Secure@10.0.10.5:5432/i9_campaigns

# 3. Criar modelos
mkdir -p app/models
touch app/models/__init__.py
touch app/models/base.py
touch app/models/campaign.py
touch app/models/image.py
touch app/models/user.py

# 4. Criar primeira migration
alembic revision --autogenerate -m "Initial migration"

# 5. Aplicar migration
alembic upgrade head

# 6. Criar script de seed
touch scripts/seed_data.py
```

## 📝 Arquivos a Criar

### app/models/base.py
```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, func
from datetime import datetime

Base = declarative_base()

class TimestampMixin:
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
```

### app/models/campaign.py
```python
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ARRAY, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.models.base import Base, TimestampMixin
import enum

class CampaignStatus(str, enum.Enum):
    ACTIVE = "active"
    SCHEDULED = "scheduled"
    PAUSED = "paused"
    EXPIRED = "expired"

class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.SCHEDULED, index=True)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    default_display_time = Column(Integer, default=5000)  # milliseconds
    stations = Column(ARRAY(String), default=list)
    priority = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)
    created_by = Column(UUID(as_uuid=True))
    
    # Relacionamentos serão adicionados depois
```

### app/models/image.py
```python
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.models.base import Base, TimestampMixin

class CampaignImage(Base, TimestampMixin):
    __tablename__ = "campaign_images"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255))
    url = Column(String(500), nullable=False)
    order = Column(Integer, nullable=False, default=0)
    display_time = Column(Integer)  # override campaign default if set
    title = Column(String(255))
    description = Column(Text)
    active = Column(Boolean, default=True)
    size_bytes = Column(Integer)
    mime_type = Column(String(50))
    width = Column(Integer)
    height = Column(Integer)
    
    # Relacionamento
    campaign = relationship("Campaign", back_populates="images")
```

### app/models/user.py
```python
from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.models.base import Base, TimestampMixin
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

class User(Base, TimestampMixin):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.VIEWER)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
```

### app/config/database.py
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config.settings import settings

# DATABASE_URL configurado em .env:
# postgresql://campaigns_user:Camp@2025#Secure@10.0.10.5:5432/i9_campaigns

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### scripts/seed_data.py
```python
#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from app.models.campaign import Campaign, CampaignStatus
from app.models.user import User, UserRole
from app.config.database import SessionLocal
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed_data():
    db = SessionLocal()
    
    # Criar usuário admin
    admin = User(
        email="admin@i9smart.com.br",
        username="admin",
        hashed_password=pwd_context.hash("admin123"),
        full_name="Administrador",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    db.add(admin)
    
    # Criar campanha exemplo
    campaign = Campaign(
        name="Campanha de Inauguração",
        description="Primeira campanha do sistema",
        status=CampaignStatus.ACTIVE,
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=30),
        default_display_time=5000,
        stations=["001", "002", "003"],
        priority=1,
        created_by=admin.id
    )
    db.add(campaign)
    
    db.commit()
    print("✅ Seed data criado com sucesso!")
    db.close()

if __name__ == "__main__":
    seed_data()
```

## ✅ Checklist de Validação

- [ ] Banco de dados criado
- [ ] Modelos definidos corretamente
- [ ] Alembic configurado
- [ ] Migrations aplicadas
- [ ] Relacionamentos funcionando
- [ ] Índices criados
- [ ] Dados de teste inseridos

## 📊 Resultado Esperado

Banco de dados estruturado com:
- Tabela `campaigns` com todas as colunas
- Tabela `campaign_images` relacionada
- Tabela `users` para autenticação
- Índices otimizados
- Constraints de integridade

Verificar:
```sql
-- No PostgreSQL
\dt
\d campaigns
\d campaign_images
\d users
```

---

*Próximo agente: A03-API-DEVELOPMENT*