#!/bin/bash

# ================================================
# Script de Backup - i9 Smart Feed API
# ================================================
# Realiza backup de dados críticos antes de deploys
# Uso: ./backup.sh [production|homolog] [full|data-only]
# ================================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parâmetros
ENV="${1:-homolog}"
BACKUP_TYPE="${2:-data-only}"

# Validar ambiente
if [ "$ENV" != "production" ] && [ "$ENV" != "homolog" ]; then
    echo -e "${RED}❌ Ambiente inválido: $ENV${NC}"
    echo -e "${YELLOW}Uso: $0 [production|homolog] [full|data-only]${NC}"
    exit 1
fi

# Validar tipo de backup
if [ "$BACKUP_TYPE" != "full" ] && [ "$BACKUP_TYPE" != "data-only" ]; then
    echo -e "${RED}❌ Tipo de backup inválido: $BACKUP_TYPE${NC}"
    echo -e "${YELLOW}Uso: $0 [production|homolog] [full|data-only]${NC}"
    exit 1
fi

# Carregar configurações
ENV_FILE=".env.deploy.${ENV}"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Arquivo $ENV_FILE não encontrado${NC}"
    exit 1
fi

source "$ENV_FILE"

# Verificar variáveis
if [ -z "$SSH_USER" ] || [ -z "$SSH_HOST" ] || [ -z "$SSH_KEY" ]; then
    echo -e "${RED}❌ Variáveis SSH não configuradas${NC}"
    exit 1
fi

# Configurações de backup
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/${SSH_USER}/backup/i9-feed"  # Usar diretório do usuário
LOCAL_BACKUP_DIR="./backups/${ENV}"
CONTAINER_NAME="i9-feed-api"
REDIS_CONTAINER="i9-feed-redis"

# Função SSH
ssh_exec() {
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ${SSH_USER}@${SSH_HOST} "$@"
}

echo -e "${BLUE}🔄 Iniciando backup ${BACKUP_TYPE} para ${ENV}...${NC}"
echo -e "${YELLOW}📅 Data: ${BACKUP_DATE}${NC}"

# 1. Criar diretórios de backup
echo -e "${YELLOW}📁 Criando estrutura de backup...${NC}"
ssh_exec "mkdir -p ${BACKUP_DIR}/{database,volumes,containers,logs}" || {
    echo -e "${YELLOW}⚠️  Tentando criar com sudo...${NC}"
    ssh_exec "sudo mkdir -p ${BACKUP_DIR}/{database,volumes,containers,logs} && sudo chown -R ${SSH_USER}:${SSH_USER} $(dirname ${BACKUP_DIR})"
}
mkdir -p "$LOCAL_BACKUP_DIR"

# 2. Backup do banco de dados
if [ "$BACKUP_TYPE" = "full" ] || [ "$BACKUP_TYPE" = "data-only" ]; then
    echo -e "${YELLOW}🗄️ Fazendo backup do banco de dados...${NC}"
    
    # Extrair URL do banco do container
    DB_BACKUP_FILE="${BACKUP_DIR}/database/db_${BACKUP_DATE}.sql"
    
    if [ "$ENV" = "production" ]; then
        ssh_exec "sudo docker exec ${CONTAINER_NAME} pg_dump \$DATABASE_URL > ${DB_BACKUP_FILE}" || \
        echo -e "${YELLOW}⚠️  Backup do banco falhou ou não aplicável${NC}"
    else
        ssh_exec "docker exec ${CONTAINER_NAME} pg_dump \$DATABASE_URL > ${DB_BACKUP_FILE}" || \
        echo -e "${YELLOW}⚠️  Backup do banco falhou ou não aplicável${NC}"
    fi
fi

# 3. Backup dos volumes Docker
if [ "$BACKUP_TYPE" = "full" ] || [ "$BACKUP_TYPE" = "data-only" ]; then
    echo -e "${YELLOW}💾 Fazendo backup dos volumes Docker...${NC}"
    
    # Lista de volumes a fazer backup
    VOLUMES=("feed-static" "feed-uploads" "feed-media" "redis-data")
    
    for volume in "${VOLUMES[@]}"; do
        echo -e "${BLUE}📦 Backup do volume: ${volume}${NC}"
        VOLUME_BACKUP="${BACKUP_DIR}/volumes/${volume}_${BACKUP_DATE}.tar.gz"
        
        if [ "$ENV" = "production" ]; then
            ssh_exec "sudo docker run --rm \
                -v ${volume}:/backup-source:ro \
                -v ${BACKUP_DIR}/volumes:/backup-dest \
                alpine:latest \
                tar -czf /backup-dest/${volume}_${BACKUP_DATE}.tar.gz -C /backup-source ." || \
            echo -e "${YELLOW}⚠️  Backup do volume ${volume} falhou${NC}"
        else
            ssh_exec "docker run --rm \
                -v ${volume}:/backup-source:ro \
                -v ${BACKUP_DIR}/volumes:/backup-dest \
                alpine:latest \
                tar -czf /backup-dest/${volume}_${BACKUP_DATE}.tar.gz -C /backup-source ." || \
            echo -e "${YELLOW}⚠️  Backup do volume ${volume} falhou${NC}"
        fi
    done
fi

# 4. Backup dos logs dos containers
echo -e "${YELLOW}📋 Fazendo backup dos logs dos containers...${NC}"
LOGS_BACKUP="${BACKUP_DIR}/logs/container_logs_${BACKUP_DATE}.tar.gz"

if [ "$ENV" = "production" ]; then
    ssh_exec "sudo docker logs ${CONTAINER_NAME} > ${BACKUP_DIR}/logs/api_${BACKUP_DATE}.log 2>&1" || true
    ssh_exec "sudo docker logs ${REDIS_CONTAINER} > ${BACKUP_DIR}/logs/redis_${BACKUP_DATE}.log 2>&1" || true
else
    ssh_exec "docker logs ${CONTAINER_NAME} > ${BACKUP_DIR}/logs/api_${BACKUP_DATE}.log 2>&1" || true
    ssh_exec "docker logs ${REDIS_CONTAINER} > ${BACKUP_DIR}/logs/redis_${BACKUP_DATE}.log 2>&1" || true
fi

# Compactar logs
ssh_exec "cd ${BACKUP_DIR}/logs && tar -czf container_logs_${BACKUP_DATE}.tar.gz *.log && rm -f *.log"

# 5. Backup da configuração atual (apenas para backup full)
if [ "$BACKUP_TYPE" = "full" ]; then
    echo -e "${YELLOW}⚙️ Fazendo backup das configurações...${NC}"
    
    CONFIG_BACKUP="${BACKUP_DIR}/containers/config_${BACKUP_DATE}.tar.gz"
    ssh_exec "cd ${REMOTE_DIR} && tar -czf ${CONFIG_BACKUP} docker-compose.yml .env Dockerfile"
    
    # Informações dos containers
    CONTAINER_INFO="${BACKUP_DIR}/containers/containers_info_${BACKUP_DATE}.json"
    if [ "$ENV" = "production" ]; then
        ssh_exec "sudo docker inspect ${CONTAINER_NAME} ${REDIS_CONTAINER} > ${CONTAINER_INFO}" || true
    else
        ssh_exec "docker inspect ${CONTAINER_NAME} ${REDIS_CONTAINER} > ${CONTAINER_INFO}" || true
    fi
fi

# 6. Criar manifesto do backup
echo -e "${YELLOW}📄 Criando manifesto do backup...${NC}"
MANIFEST="${BACKUP_DIR}/backup_manifest_${BACKUP_DATE}.json"

ssh_exec "cat > ${MANIFEST} << EOF
{
  \"backup_info\": {
    \"timestamp\": \"${BACKUP_DATE}\",
    \"environment\": \"${ENV}\",
    \"type\": \"${BACKUP_TYPE}\",
    \"server\": \"${SSH_HOST}\",
    \"user\": \"${SSH_USER}\"
  },
  \"files\": {
    \"database\": \"database/db_${BACKUP_DATE}.sql\",
    \"volumes\": [
      \"volumes/feed-static_${BACKUP_DATE}.tar.gz\",
      \"volumes/feed-uploads_${BACKUP_DATE}.tar.gz\",
      \"volumes/feed-media_${BACKUP_DATE}.tar.gz\",
      \"volumes/redis-data_${BACKUP_DATE}.tar.gz\"
    ],
    \"logs\": \"logs/container_logs_${BACKUP_DATE}.tar.gz\",
    \"config\": \"containers/config_${BACKUP_DATE}.tar.gz\"
  },
  \"restore_instructions\": {
    \"database\": \"docker exec -i container_name psql \\$DATABASE_URL < backup_file.sql\",
    \"volumes\": \"docker run --rm -v volume_name:/restore-dest -v backup_dir:/backup alpine tar -xzf /backup/volume_backup.tar.gz -C /restore-dest\",
    \"notes\": \"Restore apenas em caso de emergência. Verificar compatibilidade antes de aplicar.\"
  }
}
EOF"

# 7. Verificar tamanho do backup
echo -e "${YELLOW}📊 Verificando tamanho do backup...${NC}"
BACKUP_SIZE=$(ssh_exec "du -sh ${BACKUP_DIR} | cut -f1")
echo -e "${GREEN}📦 Tamanho total do backup: ${BACKUP_SIZE}${NC}"

# 8. Download do manifesto (para referência local)
echo -e "${YELLOW}⬇️ Baixando manifesto do backup...${NC}"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    ${SSH_USER}@${SSH_HOST}:${MANIFEST} \
    "${LOCAL_BACKUP_DIR}/backup_manifest_${BACKUP_DATE}.json"

# 9. Limpeza de backups antigos (manter últimos 5)
echo -e "${YELLOW}🧹 Limpando backups antigos...${NC}"
ssh_exec "cd ${BACKUP_DIR} && ls -1t backup_manifest_*.json | tail -n +6 | xargs -r rm -f"
ssh_exec "cd ${BACKUP_DIR}/database && ls -1t *.sql | tail -n +6 | xargs -r rm -f"
ssh_exec "cd ${BACKUP_DIR}/volumes && ls -1t *.tar.gz | tail -n +11 | xargs -r rm -f"  # 2 por tipo
ssh_exec "cd ${BACKUP_DIR}/logs && ls -1t *.tar.gz | tail -n +6 | xargs -r rm -f"

# 10. Resultado final
echo ""
echo -e "${GREEN}✅ Backup concluído com sucesso!${NC}"
echo ""
echo -e "${BLUE}📋 Informações do Backup:${NC}"
echo -e "   ${YELLOW}Ambiente:${NC} ${ENV}"
echo -e "   ${YELLOW}Tipo:${NC} ${BACKUP_TYPE}"
echo -e "   ${YELLOW}Data:${NC} ${BACKUP_DATE}"
echo -e "   ${YELLOW}Tamanho:${NC} ${BACKUP_SIZE}"
echo -e "   ${YELLOW}Servidor:${NC} ${SSH_HOST}:${BACKUP_DIR}"
echo ""
echo -e "${BLUE}📁 Arquivos de Backup:${NC}"
echo -e "   ${YELLOW}Manifesto Local:${NC} ${LOCAL_BACKUP_DIR}/backup_manifest_${BACKUP_DATE}.json"
echo -e "   ${YELLOW}Banco:${NC} ${BACKUP_DIR}/database/db_${BACKUP_DATE}.sql"
echo -e "   ${YELLOW}Volumes:${NC} ${BACKUP_DIR}/volumes/*_${BACKUP_DATE}.tar.gz"
echo -e "   ${YELLOW}Logs:${NC} ${BACKUP_DIR}/logs/container_logs_${BACKUP_DATE}.tar.gz"
if [ "$BACKUP_TYPE" = "full" ]; then
    echo -e "   ${YELLOW}Config:${NC} ${BACKUP_DIR}/containers/config_${BACKUP_DATE}.tar.gz"
fi
echo ""
echo -e "${YELLOW}💡 Para restaurar:${NC}"
echo -e "   1. Veja o manifesto para instruções específicas"
echo -e "   2. Use './restore.sh ${ENV} ${BACKUP_DATE}' (quando disponível)"
echo ""

exit 0