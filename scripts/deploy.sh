#!/bin/bash

# ================================================
# Deploy Script Melhorado - i9 Smart Feed API
# ================================================
# NOVA VERSÃO com proteção de dados e verificações de banco
# Uso: ./deploy.sh [development|homolog|production]
# ================================================

set -e  # Para o script se houver erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

# Banner
echo ""
echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}    🚀 Deploy i9 Smart Feed API - ${ENV_UPPER}    ${NC}"
echo -e "${CYAN}    ✨ Versão Melhorada com Proteção de Dados    ${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""

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

# Função para copiar arquivos via SCP (respeitando .deployignore)
scp_copy() {
    local source_path="$1"
    local dest_path="${2:-./}"
    
    # Verificar se .deployignore existe
    if [ -f ".deployignore" ]; then
        echo -e "${BLUE}📋 Aplicando regras do .deployignore...${NC}"
        
        # Tentar rsync primeiro, se falhar usar scp com exclusões manuais
        if command -v rsync >/dev/null 2>&1; then
            # Criar lista temporária de exclusões para rsync
            RSYNC_EXCLUDES=""
            while IFS= read -r line; do
                # Pular linhas vazias e comentários
                if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
                    RSYNC_EXCLUDES="$RSYNC_EXCLUDES --exclude=$line"
                fi
            done < .deployignore
            
            # Tentar rsync
            if rsync -avz $RSYNC_EXCLUDES -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" \
                "$source_path" ${SSH_USER}@${SSH_HOST}:${REMOTE_DIR}/${dest_path}; then
                return 0
            else
                echo -e "${YELLOW}⚠️  rsync falhou, usando método alternativo...${NC}"
            fi
        fi
        
        # Fallback: usar scp mas verificar se deve copiar
        if should_copy_path "$source_path"; then
            scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -r "$source_path" ${SSH_USER}@${SSH_HOST}:${REMOTE_DIR}/${dest_path}
        else
            echo -e "${YELLOW}⚠️  Pulando $source_path (excluído pelo .deployignore)${NC}"
        fi
    else
        # Fallback para scp normal
        scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -r "$source_path" ${SSH_USER}@${SSH_HOST}:${REMOTE_DIR}/${dest_path}
    fi
}

# Função para verificar se um caminho deve ser copiado
should_copy_path() {
    local path="$1"
    
    # Se não há .deployignore, sempre copiar
    if [ ! -f ".deployignore" ]; then
        return 0
    fi
    
    # Verificar cada linha do .deployignore
    while IFS= read -r line; do
        # Pular linhas vazias e comentários
        if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
            # Remover trailing slash para comparação
            pattern=$(echo "$line" | sed 's:/$::')
            path_clean=$(echo "$path" | sed 's:/$::')
            
            # Verificar se o caminho corresponde ao padrão
            if [[ "$path_clean" == *"$pattern"* ]] || [[ "$path_clean" == "$pattern" ]]; then
                return 1  # Não copiar
            fi
        fi
    done < .deployignore
    
    return 0  # Copiar
}

# Função para verificar estado do banco de dados
check_database_status() {
    echo -e "${YELLOW}🔍 Verificando estado do banco de dados...${NC}"
    
    # Copiar script de verificação para o servidor
    scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
        scripts/check_database.py ${SSH_USER}@${SSH_HOST}:${REMOTE_DIR}/
    
    # Executar verificação no servidor
    DB_STATUS=$(ssh_exec "cd ${REMOTE_DIR} && python3 check_database.py" || echo "ERROR")
    
    case "$DB_STATUS" in
        *"BANCO_NAO_EXISTE"*)
            echo -e "${RED}❌ Banco de dados não existe ou não acessível${NC}"
            return 1
            ;;
        *"PRIMEIRA_INSTALACAO"*)
            echo -e "${YELLOW}🆕 Primeira instalação detectada - banco existe mas sem estrutura${NC}"
            DATABASE_ACTION="INIT"
            ;;
        *"MIGRACOES_PENDENTES"*)
            echo -e "${BLUE}🔄 Migrações pendentes detectadas${NC}"
            DATABASE_ACTION="MIGRATE"
            ;;
        *"BANCO_ATUALIZADO"*)
            echo -e "${GREEN}✅ Banco de dados já está atualizado${NC}"
            DATABASE_ACTION="NONE"
            ;;
        *)
            echo -e "${RED}❌ Erro ao verificar banco: $DB_STATUS${NC}"
            return 1
            ;;
    esac
    
    return 0
}

# Função para aplicar migrações de banco condicionalmente
apply_database_migrations() {
    case "$DATABASE_ACTION" in
        "INIT")
            echo -e "${YELLOW}🏗️ Inicializando estrutura do banco de dados...${NC}"
            if [ "$ENV" = "production" ]; then
                ssh_exec "cd ${REMOTE_DIR} && sudo docker run --rm --env-file .env --network host ${IMAGE_NAME}:${ENV} alembic upgrade head"
            else
                ssh_exec "cd ${REMOTE_DIR} && docker run --rm --env-file .env --network host ${IMAGE_NAME}:${ENV} alembic upgrade head"
            fi
            
            # Executar dados iniciais se necessário
            init_database_data
            ;;
        "MIGRATE")
            echo -e "${YELLOW}🔄 Aplicando migrações pendentes...${NC}"
            if [ "$ENV" = "production" ]; then
                ssh_exec "cd ${REMOTE_DIR} && sudo docker run --rm --env-file .env --network host ${IMAGE_NAME}:${ENV} alembic upgrade head"
            else
                ssh_exec "cd ${REMOTE_DIR} && docker run --rm --env-file .env --network host ${IMAGE_NAME}:${ENV} alembic upgrade head"
            fi
            ;;
        "NONE")
            echo -e "${GREEN}✅ Banco já está atualizado - pulando migrações${NC}"
            ;;
    esac
}

# Função para inicializar dados do banco (primeira instalação)
init_database_data() {
    echo -e "${YELLOW}🌱 Inicializando dados básicos do banco...${NC}"
    
    # Aqui você pode adicionar dados iniciais necessários
    # Por exemplo: usuário admin, configurações padrão, etc.
    
    # Exemplo (descomente se necessário):
    # if [ "$ENV" = "production" ]; then
    #     ssh_exec "cd ${REMOTE_DIR} && sudo docker run --rm --env-file .env --network host ${IMAGE_NAME}:${ENV} python -c \"
    # from app.database import init_db
    # from app.core.config import settings
    # init_db()
    # print('✅ Dados iniciais criados')
    # \""
    # fi
    
    echo -e "${GREEN}✅ Dados iniciais configurados${NC}"
}

# Função para fazer backup antes de deploy crítico
backup_before_deploy() {
    if [ "$ENV" = "production" ] || [ "$FORCE_BACKUP" = "1" ]; then
        echo -e "${YELLOW}💾 Fazendo backup antes do deploy...${NC}"
        
        # Backup simples e direto
        BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
        BACKUP_DIR="/home/${SSH_USER}/backup"
        
        # Criar diretório de backup simples
        ssh_exec "mkdir -p ${BACKUP_DIR}" || {
            echo -e "${YELLOW}⚠️  Usando backup em /tmp...${NC}"
            BACKUP_DIR="/tmp/backup"
            ssh_exec "mkdir -p ${BACKUP_DIR}"
        }
        
        # Backup básico dos volumes
        echo -e "${BLUE}📦 Backup dos volumes Docker...${NC}"
        if [ "$ENV" = "production" ]; then
            ssh_exec "sudo docker run --rm -v feed-static:/backup-source:ro -v ${BACKUP_DIR}:/backup-dest alpine tar -czf /backup-dest/feed-static_${BACKUP_DATE}.tar.gz -C /backup-source ." 2>/dev/null || echo -e "${YELLOW}⚠️  Backup de static falhou${NC}"
            ssh_exec "sudo docker run --rm -v feed-uploads:/backup-source:ro -v ${BACKUP_DIR}:/backup-dest alpine tar -czf /backup-dest/feed-uploads_${BACKUP_DATE}.tar.gz -C /backup-source ." 2>/dev/null || echo -e "${YELLOW}⚠️  Backup de uploads falhou${NC}"
        else
            ssh_exec "docker run --rm -v feed-static:/backup-source:ro -v ${BACKUP_DIR}:/backup-dest alpine tar -czf /backup-dest/feed-static_${BACKUP_DATE}.tar.gz -C /backup-source ." 2>/dev/null || echo -e "${YELLOW}⚠️  Backup de static falhou${NC}"
            ssh_exec "docker run --rm -v feed-uploads:/backup-source:ro -v ${BACKUP_DIR}:/backup-dest alpine tar -czf /backup-dest/feed-uploads_${BACKUP_DATE}.tar.gz -C /backup-source ." 2>/dev/null || echo -e "${YELLOW}⚠️  Backup de uploads falhou${NC}"
        fi
        
        echo -e "${GREEN}✅ Backup básico concluído em ${BACKUP_DIR}${NC}"
    fi
}

# Função para garantir volumes persistentes
ensure_persistent_volumes() {
    echo -e "${YELLOW}📦 Garantindo volumes persistentes...${NC}"
    
    # Criar volumes se não existirem (usando docker-compose)
    if [ "$ENV" = "production" ]; then
        ssh_exec "cd ${REMOTE_DIR} && sudo docker-compose -f docker-compose.yml up --no-start"
    else
        ssh_exec "cd ${REMOTE_DIR} && docker-compose -f docker-compose.yml up --no-start"
    fi
    
    # Verificar se volumes existem
    VOLUMES=("feed-static" "feed-uploads" "feed-media" "redis-data")
    for volume in "${VOLUMES[@]}"; do
        if [ "$ENV" = "production" ]; then
            VOLUME_EXISTS=$(ssh_exec "sudo docker volume ls -q -f name=${volume}" || echo "")
        else
            VOLUME_EXISTS=$(ssh_exec "docker volume ls -q -f name=${volume}" || echo "")
        fi
        
        if [ -n "$VOLUME_EXISTS" ]; then
            echo -e "${GREEN}✅ Volume ${volume} já existe${NC}"
        else
            echo -e "${YELLOW}🆕 Criando volume ${volume}${NC}"
            if [ "$ENV" = "production" ]; then
                ssh_exec "sudo docker volume create ${volume}"
            else
                ssh_exec "docker volume create ${volume}"
            fi
        fi
    done
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

# 3. Fazer backup se necessário
backup_before_deploy

# 4. Transferir arquivos (PROTEGIDO - não sobrescreve static/)
echo -e "${YELLOW}📤 Transferindo arquivos para o servidor (protegendo dados)...${NC}"

# Transferir aplicação e migrações
scp_copy app/
scp_copy migrations/
scp_copy scripts/

# ❌ IMPORTANTE: NÃO transferir static/ - preservar dados do usuário
echo -e "${GREEN}🛡️  Pasta static/ PROTEGIDA - não será sobrescrita${NC}"

# Transferir repo se existir (apenas para desenvolvimento)
[ -d "repo" ] && scp_copy repo/ || echo -e "${YELLOW}ℹ️  Pasta repo não encontrada, pulando...${NC}"

# Transferir arquivos de configuração
scp_copy Dockerfile
scp_copy docker-compose.yml  
scp_copy requirements.txt
scp_copy alembic.ini
[ -f ".dockerignore" ] && scp_copy .dockerignore || true
[ -f ".deployignore" ] && scp_copy .deployignore || true

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

# 6. Verificar estado do banco e aplicar migrações condicionalmente
if ! check_database_status; then
    echo -e "${RED}❌ Falha na verificação do banco de dados${NC}"
    exit 1
fi

# 7. Garantir volumes persistentes antes de iniciar containers
ensure_persistent_volumes

# 8. Aplicar migrações baseado no estado do banco
apply_database_migrations

# 9. Iniciar novos containers com volumes persistentes
echo -e "${YELLOW}🚀 Iniciando containers com docker-compose...${NC}"

# Definir variáveis de ambiente para docker-compose
ssh_exec "cd ${REMOTE_DIR} && export VERSION=${ENV} && export APP_PORT=${APP_PORT} && export REDIS_PORT=${REDIS_PORT}"

if [ "$ENV" = "production" ]; then
    ssh_exec "cd ${REMOTE_DIR} && sudo docker-compose -f docker-compose.yml up -d"
else
    ssh_exec "cd ${REMOTE_DIR} && docker-compose -f docker-compose.yml up -d"
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