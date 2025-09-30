#!/bin/bash

# ================================================
# Deploy Script para i9 Smart Campaigns API
# ================================================
# Uso: ./deploy.sh [homolog|production]
# ================================================

set -e  # Exit on error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Timestamp para logs
timestamp() {
    date +"%Y-%m-%d %H:%M:%S"
}

# Função de log
log() {
    echo -e "${BLUE}[$(timestamp)]${NC} $1"
}

error() {
    echo -e "${RED}[$(timestamp)] ERROR:${NC} $1" >&2
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(timestamp)] WARNING:${NC} $1"
}

success() {
    echo -e "${GREEN}[$(timestamp)] SUCCESS:${NC} $1"
}

# ================================================
# CONFIGURAÇÕES
# ================================================

# Detectar ambiente
ENVIRONMENT=${1:-homolog}

# Validar ambiente
if [[ "$ENVIRONMENT" != "homolog" && "$ENVIRONMENT" != "production" ]]; then
    error "Ambiente inválido: $ENVIRONMENT. Use 'homolog' ou 'production'"
fi

# Carregar variáveis de ambiente
if [ -f ".env.deploy" ]; then
    source .env.deploy
else
    error "Arquivo .env.deploy não encontrado. Execute 'make setup-ssh' primeiro."
fi

# Configurações do servidor
SSH_ALIAS=${SSH_ALIAS:-i9-deploy}
SSH_USER=${SSH_USER:-lee}
SSH_HOST=${SSH_HOST:-10.0.20.11}
SSH_PORT=${SSH_PORT:-22}

# Configurações do projeto
PROJECT_NAME="i9-campaigns-api"
REMOTE_DIR="/docker/i9-smart/campaigns_api"  # Note o _api aqui
IMAGE_NAME="i9-campaigns-api"
CONTAINER_NAME="i9-campaigns-api"
REDIS_CONTAINER="i9-campaigns-redis"

# Portas
if [ "$ENVIRONMENT" == "production" ]; then
    APP_PORT=8000
    REDIS_PORT=6379
    VERSION="latest"
    ENV_FILE=".env.production"
else
    APP_PORT=8001
    REDIS_PORT=6380
    VERSION="homolog"
    ENV_FILE=".env"
fi

# SSH command alias - Usando o alias configurado
SSH_CMD="ssh $SSH_ALIAS"
SCP_CMD="scp"

# ================================================
# PRÉ-VERIFICAÇÕES
# ================================================

log "🔍 Verificando pré-requisitos..."

# Verificar arquivos necessários
REQUIRED_FILES=("Dockerfile" "docker-compose.yml" "requirements.txt" "$ENV_FILE" "alembic.ini")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        error "Arquivo necessário não encontrado: $file"
    fi
done

# Verificar diretórios necessários
REQUIRED_DIRS=("app" "migrations" "static" "repo")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        warning "Diretório não encontrado: $dir - criando..."
        mkdir -p "$dir"
    fi
done

# Testar conexão SSH
log "🔗 Testando conexão SSH..."
$SSH_CMD "echo 'SSH connection successful'" || error "Falha na conexão SSH"

# ================================================
# PREPARAÇÃO
# ================================================

log "📦 Preparando deploy para ambiente: ${YELLOW}$ENVIRONMENT${NC}"

# Criar arquivo .env temporário com as variáveis necessárias
if [ "$ENVIRONMENT" == "production" ]; then
    if [ ! -f ".env.production" ]; then
        error "Arquivo .env.production não encontrado"
    fi
    cp .env.production .env.deploy.tmp
else
    cp .env .env.deploy.tmp
fi

# Adicionar VERSION ao arquivo de ambiente
echo "VERSION=$VERSION" >> .env.deploy.tmp

# ================================================
# DEPLOY
# ================================================

log "🚀 Iniciando deploy..."

# 1. Criar estrutura de diretórios no servidor
log "📁 Criando estrutura de diretórios no servidor..."
$SSH_CMD "mkdir -p $REMOTE_DIR/{app,migrations,static,repo}"

# 2. Transferir arquivos
log "📤 Transferindo arquivos para o servidor..."

# Transferir aplicação - Usando o alias SSH
$SCP_CMD -r app/* $SSH_ALIAS:$REMOTE_DIR/app/
$SCP_CMD -r migrations/* $SSH_ALIAS:$REMOTE_DIR/migrations/
$SCP_CMD -r static/* $SSH_ALIAS:$REMOTE_DIR/static/ 2>/dev/null || warning "Pasta static vazia ou não existe"
$SCP_CMD -r repo/* $SSH_ALIAS:$REMOTE_DIR/repo/ 2>/dev/null || warning "Pasta repo vazia ou não existe"

# Transferir arquivos de configuração
$SCP_CMD requirements.txt $SSH_ALIAS:$REMOTE_DIR/
$SCP_CMD Dockerfile $SSH_ALIAS:$REMOTE_DIR/
$SCP_CMD docker-compose.yml $SSH_ALIAS:$REMOTE_DIR/
$SCP_CMD alembic.ini $SSH_ALIAS:$REMOTE_DIR/
$SCP_CMD .dockerignore $SSH_ALIAS:$REMOTE_DIR/ 2>/dev/null || true
$SCP_CMD .env.deploy.tmp $SSH_ALIAS:$REMOTE_DIR/.env

# Limpar arquivo temporário
rm -f .env.deploy.tmp

# 3. Build da imagem Docker
log "🔨 Construindo imagem Docker..."
$SSH_CMD "cd $REMOTE_DIR && docker build -t $IMAGE_NAME:$VERSION ."

# 4. Parar containers existentes
log "🛑 Parando containers existentes..."
$SSH_CMD "docker stop $CONTAINER_NAME 2>/dev/null || true"
$SSH_CMD "docker stop $REDIS_CONTAINER 2>/dev/null || true"
$SSH_CMD "docker rm $CONTAINER_NAME 2>/dev/null || true"
$SSH_CMD "docker rm $REDIS_CONTAINER 2>/dev/null || true"

# 5. Executar migrações de banco de dados
log "🗄️ Executando migrações de banco de dados..."
$SSH_CMD "cd $REMOTE_DIR && docker run --rm \
    --env-file .env \
    --network host \
    $IMAGE_NAME:$VERSION \
    alembic upgrade head" || warning "Falha ao executar migrações"

# 6. Iniciar novos containers
log "▶️ Iniciando novos containers..."
$SSH_CMD "cd $REMOTE_DIR && docker-compose up -d"

# 7. Aguardar containers iniciarem
log "⏳ Aguardando containers iniciarem..."
sleep 10

# 8. Verificar status dos containers
log "✅ Verificando status dos containers..."
CONTAINER_STATUS=$($SSH_CMD "docker ps --filter name=$CONTAINER_NAME --format '{{.Status}}'")
REDIS_STATUS=$($SSH_CMD "docker ps --filter name=$REDIS_CONTAINER --format '{{.Status}}'")

if [[ $CONTAINER_STATUS == *"Up"* ]]; then
    success "Container API rodando: $CONTAINER_STATUS"
else
    error "Container API não está rodando"
fi

if [[ $REDIS_STATUS == *"Up"* ]]; then
    success "Container Redis rodando: $REDIS_STATUS"
else
    warning "Container Redis não está rodando"
fi

# 9. Verificar logs
log "📋 Últimas linhas dos logs:"
$SSH_CMD "docker logs --tail 20 $CONTAINER_NAME"

# 10. Testar endpoint de health
log "🏥 Testando endpoint de health..."
sleep 5
HEALTH_CHECK=$($SSH_CMD "curl -s -o /dev/null -w '%{http_code}' http://localhost:$APP_PORT/health")

if [ "$HEALTH_CHECK" == "200" ]; then
    success "Health check OK (HTTP $HEALTH_CHECK)"
else
    warning "Health check retornou HTTP $HEALTH_CHECK"
fi

# 11. Limpeza de imagens antigas
log "🧹 Limpando imagens Docker antigas..."
$SSH_CMD "docker image prune -f" > /dev/null 2>&1

# ================================================
# FINALIZAÇÃO
# ================================================

echo ""
success "🎉 Deploy concluído com sucesso!"
echo ""
echo -e "${GREEN}Informações do Deploy:${NC}"
echo -e "  📍 Servidor: $SSH_HOST"
echo -e "  🌍 Ambiente: $ENVIRONMENT"
echo -e "  🏷️  Versão: $VERSION"
echo -e "  🚪 Porta API: $APP_PORT"
echo -e "  🚪 Porta Redis: $REDIS_PORT"
echo -e "  📦 Container: $CONTAINER_NAME"
echo ""
echo -e "${YELLOW}URLs de Acesso:${NC}"
echo -e "  🔗 API: http://$SSH_HOST:$APP_PORT"
echo -e "  📚 Docs: http://$SSH_HOST:$APP_PORT/docs"
echo -e "  📊 ReDoc: http://$SSH_HOST:$APP_PORT/redoc"
echo ""
echo -e "${BLUE}Comandos úteis:${NC}"
echo -e "  Ver logs: make deploy-logs"
echo -e "  Status: make deploy-status"
echo -e "  Restart: make deploy-restart"
echo -e "  SSH: make deploy-ssh"
echo ""

# Se for produção, perguntar sobre tag
if [ "$ENVIRONMENT" == "production" ]; then
    read -p "Deseja criar uma tag para esta versão? (s/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        read -p "Digite o número da versão (ex: 1.0.0): " VERSION_TAG
        if [ ! -z "$VERSION_TAG" ]; then
            git tag -a "v$VERSION_TAG" -m "Deploy to production v$VERSION_TAG"
            git push origin "v$VERSION_TAG"
            success "Tag v$VERSION_TAG criada e enviada"
        fi
    fi
fi

exit 0