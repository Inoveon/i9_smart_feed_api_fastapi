# A01 - Setup Environment

## 📋 Objetivo
Configurar o ambiente de desenvolvimento completo para a API de Campanhas, incluindo Python, dependências, banco de dados e ferramentas.

## 🎯 Tarefas

### 1. Ambiente Python
- [ ] Criar virtual environment .venv Python 3.11+
- [ ] Instalar pip-tools para gerenciamento de dependências
- [ ] Criar requirements.in com dependências principais
- [ ] Compilar requirements.txt
- [ ] Instalar todas as dependências

### 2. Arquivos de Configuração
- [ ] Criar .env.example com todas as variáveis
- [ ] Criar .env local para desenvolvimento
- [ ] Criar .gitignore apropriado
- [ ] Criar estrutura de pastas faltantes

### 3. Docker Setup
- [ ] Criar Dockerfile para a API
- [ ] Criar docker-compose.yml com serviços
- [ ] Configurar PostgreSQL container
- [ ] Configurar Redis container
- [ ] Configurar MinIO container

### 4. Configuração da Aplicação
- [ ] Criar app/main.py com FastAPI básico
- [ ] Criar app/config/settings.py com Pydantic Settings
- [ ] Configurar CORS
- [ ] Configurar middleware de logging

## 🔧 Comandos

```bash
# 1. Criar ambiente virtual com .venv
cd /Users/leechardes/Projetos/i9_smart/apis/i9_smart_campaigns_api_fastapi
python3.11 -m venv .venv
source .venv/bin/activate

# 2. Instalar pip-tools
pip install pip-tools

# 3. Criar requirements.in
cat > requirements.in << 'EOF'
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
python-dotenv==1.0.0
httpx==0.26.0
EOF

# 4. Compilar requirements.txt
pip-compile requirements.in

# 5. Instalar dependências
pip install -r requirements.txt

# 6. Criar .env.example
cat > .env.example << 'EOF'
# Application
APP_NAME=i9 Smart Campaigns API
APP_VERSION=1.0.0
DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production
ENVIRONMENT=development

# API Keys
API_KEY_TABLETS=i9smart_campaigns_readonly_2025

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://campaigns:campaigns123@localhost:5432/i9_campaigns

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO/S3
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=campaigns
MINIO_SECURE=False

# JWT
JWT_SECRET_KEY=your-jwt-secret-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Uploads
MAX_UPLOAD_SIZE=10485760
ALLOWED_EXTENSIONS=jpg,jpeg,png,webp
EOF

# 7. Criar .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment
.env
.env.local
.env.*.local

# Database
*.db
*.sqlite3

# Uploads
uploads/
static/uploads/

# Logs
logs/
*.log

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/

# OS
.DS_Store
Thumbs.db

# Docker
docker-compose.override.yml
EOF

# 8. Criar estrutura de pastas adicionais
mkdir -p app/{middleware,dependencies,utils}
mkdir -p static/uploads
mkdir -p logs

# 9. Docker setup
echo "Docker files criados - execute docker-compose up -d quando pronto"
```

## 📝 Arquivos a Criar

### app/main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "i9 Smart Campaigns API", "version": settings.APP_VERSION}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### app/config/settings.py
```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # App
    APP_NAME: str = "i9 Smart Campaigns API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str
    ENVIRONMENT: str = "development"
    
    # API Keys
    API_KEY_TABLETS: str
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # MinIO
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "campaigns"
    MINIO_SECURE: bool = False
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440
    
    # CORS
    CORS_ORIGINS: List[str] = []
    
    # Uploads
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "webp"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

settings = Settings()
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: campaigns
      POSTGRES_PASSWORD: campaigns123
      POSTGRES_DB: i9_campaigns
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  minio_data:
```

## ✅ Checklist de Validação

- [ ] Virtual environment .venv criado e ativado
- [ ] Todas as dependências instaladas
- [ ] Makefile funcionando corretamente
- [ ] .env configurado com valores locais
- [ ] Docker containers rodando
- [ ] FastAPI respondendo em http://localhost:8000
- [ ] Documentação em http://localhost:8000/docs
- [ ] PostgreSQL acessível
- [ ] Redis funcionando
- [ ] MinIO console em http://localhost:9001

## 📊 Resultado Esperado

Ao final, você deve ter:
1. Ambiente Python .venv configurado
2. Todas as dependências instaladas
3. Serviços Docker rodando
4. API básica funcionando
5. Estrutura de pastas completa
6. Makefile com comandos de automação

Para testar:
```bash
# Usando Makefile
make install  # Instalar dependências
make dev      # Iniciar servidor de desenvolvimento

# Ou manualmente
source .venv/bin/activate
uvicorn app.main:app --reload

# Verificar
curl http://localhost:8000/health
```

---

*Próximo agente: A02-DATABASE-SETUP*