# 🌍 Ambientes - i9 Smart Feed API

Configuração e detalhes dos ambientes de desenvolvimento, homologação e produção.

## 📊 Resumo dos Ambientes

| Ambiente | Servidor | Usuário | Porta | Finalidade |
|----------|----------|---------|-------|------------|
| Development | localhost | - | 8000 | Desenvolvimento local |
| Homologação | 10.0.20.11 | lee | 8001 | Testes e validação |
| Produção | 172.16.2.90 | i9on | 8000 | Ambiente live |

## 🔧 Development (Desenvolvimento Local)

### Configuração
- **Host**: localhost
- **Porta**: 8000
- **Banco**: SQLite local ou PostgreSQL local
- **Redis**: Instância local (porta 6379)

### Características
- Hot reload ativado
- Debug habilitado
- Logs detalhados
- Sem autenticação SSH necessária

### Como Usar
```bash
# Opção 1: Via deploy script
make deploy-development

# Opção 2: Direto
make dev

# Opção 3: Manual
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### URLs
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Homologação

### Configuração
- **Servidor**: 10.0.20.11
- **Usuário SSH**: lee
- **Porta API**: 8001
- **Porta Redis**: 6380
- **Diretório**: `/docker/i9-smart/feed-api`

### Características
- Ambiente espelho da produção
- Dados de teste
- Ideal para validação antes da produção
- Acesso via SSH com chave

### Configuração SSH
```bash
# Arquivo: .env.deploy.homolog
export SSH_USER="lee"
export SSH_HOST="10.0.20.11"
export SSH_KEY="$HOME/.ssh/id_rsa_i9_deploy"
export REMOTE_DIR="/docker/i9-smart/feed-api"
export APP_PORT="8001"
export REDIS_PORT="6380"
```

### Deploy
```bash
make deploy-homolog
```

### URLs
- **API**: http://10.0.20.11:8001
- **Docs**: http://10.0.20.11:8001/docs
- **ReDoc**: http://10.0.20.11:8001/redoc
- **Health**: http://10.0.20.11:8001/health

## 🏭 Produção

### Configuração
- **Servidor**: 172.16.2.90
- **Usuário SSH**: i9on
- **Senha SSH**: aldo$2024
- **Porta API**: 8000
- **Porta Redis**: 6379
- **Diretório**: `/docker/i9-smart/feed-api`

### Características
- Ambiente live para usuários finais
- Dados reais de produção
- Alta disponibilidade
- Comandos executados com sudo
- Confirmação obrigatória para deploy

### Configuração SSH
```bash
# Arquivo: .env.deploy.production
export SSH_USER="i9on"
export SSH_HOST="172.16.2.90"
export SSH_KEY="$HOME/.ssh/id_rsa_i9_deploy"
export REMOTE_DIR="/docker/i9-smart/feed-api"
export APP_PORT="8000"
export REDIS_PORT="6379"
```

### Deploy
```bash
make deploy-production
# Requer confirmação manual
```

### URLs
- **API**: http://172.16.2.90:8000
- **Docs**: http://172.16.2.90:8000/docs
- **ReDoc**: http://172.16.2.90:8000/redoc
- **Health**: http://172.16.2.90:8000/health

## 🔑 Autenticação SSH

### Chave Unificada
Todos os ambientes usam a mesma chave SSH:
- **Arquivo**: `~/.ssh/id_rsa_i9_deploy`
- **Configuração**: Automática via `make setup-ssh`

### Configuração Manual
```bash
# Gerar chave (se não existir)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_i9_deploy -N ""

# Copiar para homologação
ssh-copy-id -i ~/.ssh/id_rsa_i9_deploy.pub lee@10.0.20.11

# Copiar para produção (com senha)
sshpass -p 'aldo$2024' ssh-copy-id -i ~/.ssh/id_rsa_i9_deploy.pub i9on@172.16.2.90
```

## 🐳 Containers Docker

### Estrutura Comum
Cada ambiente executa os seguintes containers:

1. **API Container** (`i9-feed-api`)
   - Imagem: `i9-feed-api:{environment}`
   - Porta: Conforme configuração do ambiente
   - Volumes: Logs, uploads, cache

2. **Redis Container** (`i9-feed-redis`)
   - Imagem: `redis:alpine`
   - Porta: Conforme configuração do ambiente
   - Dados: Cache, sessões

### Comandos Docker por Ambiente

#### Homologação
```bash
# Ver containers
docker ps --filter name=i9-feed

# Logs da API
docker logs -f i9-feed-api

# Acessar container
docker exec -it i9-feed-api /bin/bash
```

#### Produção
```bash
# Ver containers (com sudo)
sudo docker ps --filter name=i9-feed

# Logs da API (com sudo)
sudo docker logs -f i9-feed-api

# Acessar container (com sudo)
sudo docker exec -it i9-feed-api /bin/bash
```

## 🗃️ Banco de Dados

### Development
- **Tipo**: SQLite ou PostgreSQL local
- **Arquivo**: `./app.db` (SQLite)
- **URL**: `sqlite:///./app.db`

### Homologação
- **Tipo**: PostgreSQL
- **Host**: Configurado no `.env`
- **Porta**: 5432
- **Database**: `i9_feed_homolog`

### Produção
- **Tipo**: PostgreSQL
- **Host**: Configurado no `.env.production`
- **Porta**: 5432
- **Database**: `i9_feed_production`

## 📝 Variáveis de Ambiente

### Arquivo .env (Local/Homolog)
```bash
# Application
APP_NAME=i9 Smart Feed API
DEBUG=True
SECRET_KEY=dev-secret-key

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys
API_KEY_TABLETS=dev-api-key
```

### Arquivo .env.production (Produção)
```bash
# Application
APP_NAME=i9 Smart Feed API
DEBUG=False
SECRET_KEY=production-secret-key

# Database
DATABASE_URL=postgresql://user:pass@host:5432/i9_feed_production

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys
API_KEY_TABLETS=production-api-key
```

## 🔄 Fluxo de Deploy

### 1. Desenvolvimento → Homologação
```bash
# No desenvolvimento
git add -A
git commit -m "feat: nova funcionalidade"
git push origin main

# Deploy para homolog
make deploy-homolog
```

### 2. Homologação → Produção
```bash
# Testar em homolog
curl http://10.0.20.11:8001/health

# Se OK, deploy para produção
make deploy-production
```

## 🚨 Monitoramento

### Health Checks
Todos os ambientes possuem endpoint de health:
- **URL**: `/health`
- **Resposta**: Status da API, banco e Redis

### Logs
```bash
# Desenvolvimento
tail -f logs/app.log

# Homologação/Produção
make deploy-logs
```

### Métricas
- **CPU/Memoria**: via `docker stats`
- **Aplicação**: Logs estruturados
- **Uptime**: Health check endpoint

## 🔧 Manutenção

### Backup (Produção)
```bash
# Backup do banco
pg_dump -h host -U user -d i9_feed_production > backup.sql

# Backup dos uploads
tar -czf uploads-backup.tar.gz static/uploads/
```

### Atualizações
```bash
# Atualizar dependências
pip install -r requirements.txt

# Executar migrações
alembic upgrade head

# Reiniciar serviços
make deploy-restart
```

## 📞 Suporte

### Acesso aos Servidores
- **Homologação**: `ssh lee@10.0.20.11`
- **Produção**: `ssh i9on@172.16.2.90`

### Comandos Úteis
```bash
# Status geral
make deploy-info

# Conexão SSH
make deploy-ssh

# Limpeza
make deploy-clean
```

### Contato
- **Responsável**: Lee Chardes
- **Email**: lee@inoveon.com.br

---

**Última atualização**: 30/09/2025