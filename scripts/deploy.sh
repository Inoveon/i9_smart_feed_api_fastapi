#!/bin/bash

# Deploy Script Unificado para i9 Smart Feed API
# Uso: ./deploy.sh [development|homolog|production]

set -e  # Para o script se houver erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Determinar ambiente
ENV="${1:-homolog}"

# Validar ambiente
if [ "$ENV" != "development" ] && [ "$ENV" != "homolog" ] && [ "$ENV" != "production" ]; then
    echo -e "${RED}❌ Ambiente inválido: $ENV${NC}"
    echo -e "${YELLOW}Uso: $0 [development|homolog|production]${NC}"
    exit 1
fi

# Configurações comuns
IMAGE_NAME="i9-feed-api"
CONTAINER_NAME="i9-feed-api"
REDIS_CONTAINER="i9-feed-redis"

ENV_UPPER=$(echo "$ENV" | tr '[:lower:]' '[:upper:]')
echo -e "${GREEN}🚀 Deploy para ${ENV_UPPER}${NC}"

# Tratamento para desenvolvimento
if [ "$ENV" = "development" ]; then
    echo -e "${YELLOW}📦 Iniciando ambiente de desenvolvimento...${NC}"
    echo -e "${BLUE}API: http://localhost:8000${NC}"
    echo -e "${BLUE}Docs: http://localhost:8000/docs${NC}"
    make dev
    exit 0
fi

# Carregar variáveis de ambiente para homolog/production
ENV_FILE=".env.deploy.${ENV}"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Arquivo $ENV_FILE não encontrado${NC}"
    echo -e "${YELLOW}Crie o arquivo com as configurações do ambiente${NC}"
    exit 1
fi

source $ENV_FILE

# Verificar variáveis obrigatórias
if [ -z "$SSH_USER" ] || [ -z "$SSH_HOST" ] || [ -z "$SSH_KEY" ] || [ -z "$REMOTE_DIR" ]; then
    echo -e "${RED}❌ Variáveis de ambiente incompletas em $ENV_FILE${NC}"
    echo -e "${YELLOW}Verifique SSH_USER, SSH_HOST, SSH_KEY e REMOTE_DIR${NC}"
    exit 1
fi

# Verificar se a chave SSH existe
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}❌ Chave SSH não encontrada em: $SSH_KEY${NC}"
    echo -e "${BLUE}Execute: ${GREEN}make setup-ssh${NC} para configurar a autenticação SSH"
    exit 1
fi

# Função para executar comandos SSH
ssh_exec() {
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${SSH_USER}@${SSH_HOST} "$@"
}

# Função para copiar arquivos via SCP
scp_copy() {
    scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -r "$@" ${SSH_USER}@${SSH_HOST}:${REMOTE_DIR}/
}

echo -e "${YELLOW}📍 Servidor: ${SSH_HOST}${NC}"
echo -e "${YELLOW}👤 Usuário: ${SSH_USER}${NC}"
echo -e "${YELLOW}📁 Diretório: ${REMOTE_DIR}${NC}"

# Confirmação para produção (pular se SKIP_CONFIRM=1)
if [ "$ENV" = "production" ] && [ "$SKIP_CONFIRM" != "1" ]; then
    echo ""
    echo -e "${RED}⚠️  ATENÇÃO: Deploy para PRODUÇÃO!${NC}"
    read -p "Confirma deploy para produção? (s/N): " confirm
    if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
        echo -e "${YELLOW}Deploy cancelado${NC}"
        exit 1
    fi
fi

# 1. Verificar pré-requisitos locais
echo -e "${YELLOW}🔍 Verificando pré-requisitos...${NC}"

REQUIRED_FILES=("Dockerfile" "docker-compose.yml" "requirements.txt" "alembic.ini")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ Arquivo necessário não encontrado: $file${NC}"
        exit 1
    fi
done

REQUIRED_DIRS=("app" "migrations")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo -e "${RED}❌ Diretório necessário não encontrado: $dir${NC}"
        exit 1
    fi
done

# 2. Criar estrutura no servidor (se não existir)
echo -e "${YELLOW}📁 Criando estrutura de diretórios no servidor...${NC}"
if [ "$ENV" = "production" ]; then
    # Para produção, precisa criar com sudo se não existir
    ssh_exec "if [ ! -d '${REMOTE_DIR}' ]; then sudo mkdir -p ${REMOTE_DIR} && sudo chown -R ${SSH_USER}:${SSH_USER} ${REMOTE_DIR}; else echo 'Diretório já existe'; fi"
else
    # Para homologação, tenta sem sudo primeiro
    ssh_exec "mkdir -p ${REMOTE_DIR} 2>/dev/null || true"
fi

# Criar subdiretórios
ssh_exec "mkdir -p ${REMOTE_DIR}/{app,migrations,static,repo}"

# 3. Transferir arquivos
echo -e "${YELLOW}📤 Transferindo arquivos para o servidor...${NC}"

# Transferir aplicação
scp_copy app/
scp_copy migrations/
[ -d "static" ] && scp_copy static/ || echo -e "${YELLOW}ℹ️  Pasta static não encontrada, pulando...${NC}"
[ -d "repo" ] && scp_copy repo/ || echo -e "${YELLOW}ℹ️  Pasta repo não encontrada, pulando...${NC}"

# Transferir arquivos de configuração
scp_copy Dockerfile docker-compose.yml requirements.txt alembic.ini
[ -f ".dockerignore" ] && scp_copy .dockerignore || true

# Transferir arquivo de ambiente apropriado
if [ "$ENV" = "production" ] && [ -f ".env.production" ]; then
    scp -i "$SSH_KEY" -o StrictHostKeyChecking=no .env.production ${SSH_USER}@${SSH_HOST}:${REMOTE_DIR}/.env
else
    # Para homologação, usar .env padrão se existir
    [ -f ".env" ] && scp -i "$SSH_KEY" -o StrictHostKeyChecking=no .env ${SSH_USER}@${SSH_HOST}:${REMOTE_DIR}/.env || true
fi

# 4. Build da imagem Docker no servidor
echo -e "${YELLOW}🐳 Fazendo build da imagem Docker...${NC}"
if [ "$ENV" = "production" ]; then
    ssh_exec "cd ${REMOTE_DIR} && sudo docker build -t ${IMAGE_NAME}:${ENV} ."
else
    ssh_exec "cd ${REMOTE_DIR} && docker build -t ${IMAGE_NAME}:${ENV} ."
fi

# 5. Parar containers anteriores (se existirem)
echo -e "${YELLOW}🛑 Parando containers anteriores (se existirem)...${NC}"
if [ "$ENV" = "production" ]; then
    ssh_exec "sudo docker stop ${CONTAINER_NAME} ${REDIS_CONTAINER} 2>/dev/null || true && sudo docker rm ${CONTAINER_NAME} ${REDIS_CONTAINER} 2>/dev/null || true"
else
    ssh_exec "docker stop ${CONTAINER_NAME} ${REDIS_CONTAINER} 2>/dev/null || true && docker rm ${CONTAINER_NAME} ${REDIS_CONTAINER} 2>/dev/null || true"
fi

# 6. Executar migrações de banco de dados
echo -e "${YELLOW}🗄️ Executando migrações de banco de dados...${NC}"
if [ "$ENV" = "production" ]; then
    ssh_exec "cd ${REMOTE_DIR} && sudo docker run --rm --env-file .env --network host ${IMAGE_NAME}:${ENV} alembic upgrade head" || echo -e "${YELLOW}⚠️  Migrações falharam ou não necessárias${NC}"
else
    ssh_exec "cd ${REMOTE_DIR} && docker run --rm --env-file .env --network host ${IMAGE_NAME}:${ENV} alembic upgrade head" || echo -e "${YELLOW}⚠️  Migrações falharam ou não necessárias${NC}"
fi

# 7. Iniciar novos containers
echo -e "${YELLOW}🚀 Iniciando novos containers...${NC}"
if [ "$ENV" = "production" ]; then
    ssh_exec "cd ${REMOTE_DIR} && sudo docker run -d --name ${CONTAINER_NAME} -p ${APP_PORT}:8000 --env-file .env --restart unless-stopped ${IMAGE_NAME}:${ENV}"
    # Iniciar Redis se necessário
    ssh_exec "sudo docker run -d --name ${REDIS_CONTAINER} -p ${REDIS_PORT}:6379 --restart unless-stopped redis:alpine" 2>/dev/null || echo -e "${YELLOW}ℹ️  Redis já rodando ou não necessário${NC}"
else
    ssh_exec "cd ${REMOTE_DIR} && docker run -d --name ${CONTAINER_NAME} -p ${APP_PORT}:8000 --env-file .env --restart unless-stopped ${IMAGE_NAME}:${ENV}"
    # Iniciar Redis se necessário
    ssh_exec "docker run -d --name ${REDIS_CONTAINER} -p ${REDIS_PORT}:6379 --restart unless-stopped redis:alpine" 2>/dev/null || echo -e "${YELLOW}ℹ️  Redis já rodando ou não necessário${NC}"
fi

# 8. Verificar se está rodando
echo -e "${YELLOW}✅ Verificando status...${NC}"
sleep 5
if [ "$ENV" = "production" ]; then
    ssh_exec "sudo docker ps | grep ${CONTAINER_NAME} || echo '⚠️ Container da API não encontrado'"
    ssh_exec "sudo docker ps | grep ${REDIS_CONTAINER} || echo '⚠️ Container do Redis não encontrado'"
else
    ssh_exec "docker ps | grep ${CONTAINER_NAME} || echo '⚠️ Container da API não encontrado'"
    ssh_exec "docker ps | grep ${REDIS_CONTAINER} || echo '⚠️ Container do Redis não encontrado'"
fi

# 9. Mostrar logs iniciais
echo -e "${YELLOW}📋 Logs iniciais da API:${NC}"
if [ "$ENV" = "production" ]; then
    ssh_exec "sudo docker logs --tail 20 ${CONTAINER_NAME}"
else
    ssh_exec "docker logs --tail 20 ${CONTAINER_NAME}"
fi

# 10. Testar endpoint de health
echo -e "${YELLOW}🏥 Testando endpoint de health...${NC}"
sleep 5
HEALTH_CHECK=$(ssh_exec "curl -s -o /dev/null -w '%{http_code}' http://localhost:${APP_PORT}/health" || echo "000")

if [ "$HEALTH_CHECK" == "200" ]; then
    echo -e "${GREEN}✅ Health check OK (HTTP $HEALTH_CHECK)${NC}"
else
    echo -e "${YELLOW}⚠️  Health check retornou HTTP $HEALTH_CHECK${NC}"
fi

echo -e "${GREEN}✅ Deploy concluído com sucesso!${NC}"
echo -e "${GREEN}🌐 API disponível em: http://${SSH_HOST}:${APP_PORT}${NC}"

# Mostrar informações de conexão
echo ""
echo -e "${BLUE}📋 Informações de Deploy:${NC}"
echo -e "   ${YELLOW}Ambiente:${NC} ${ENV_UPPER}"
echo -e "   ${YELLOW}Servidor:${NC} ${SSH_USER}@${SSH_HOST}"
echo -e "   ${YELLOW}Container API:${NC} ${CONTAINER_NAME}"
echo -e "   ${YELLOW}Container Redis:${NC} ${REDIS_CONTAINER}"
echo -e "   ${YELLOW}Imagem:${NC} ${IMAGE_NAME}:${ENV}"
echo -e "   ${YELLOW}Porta API:${NC} ${APP_PORT}"
echo -e "   ${YELLOW}Porta Redis:${NC} ${REDIS_PORT}"
echo -e "   ${YELLOW}Diretório:${NC} ${REMOTE_DIR}"
echo ""
echo -e "${BLUE}🔗 URLs de Acesso:${NC}"
echo -e "   ${YELLOW}API:${NC} http://${SSH_HOST}:${APP_PORT}"
echo -e "   ${YELLOW}Docs:${NC} http://${SSH_HOST}:${APP_PORT}/docs"
echo -e "   ${YELLOW}ReDoc:${NC} http://${SSH_HOST}:${APP_PORT}/redoc"
echo -e "   ${YELLOW}Health:${NC} http://${SSH_HOST}:${APP_PORT}/health"
echo ""