#!/bin/bash

# ================================================
# Setup SSH para Deploy Automatizado
# ================================================
# Este script configura autenticação SSH por chave
# Execute apenas uma vez antes do primeiro deploy
# ================================================

set -e  # Exit on error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo ""
echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}     Setup SSH - i9 Smart Campaigns API        ${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""

# Função de log
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# ================================================
# CONFIGURAÇÕES
# ================================================

# Arquivo de configuração
ENV_FILE=".env.deploy"
SSH_CONFIG_FILE="$HOME/.ssh/config"

# Nome do projeto
PROJECT_NAME="i9-campaigns-api"

# Servidor padrão
DEFAULT_HOST="10.0.20.11"
DEFAULT_USER="lee"
DEFAULT_PORT="22"

# Chave SSH dedicada
SSH_KEY_NAME="id_rsa_i9_campaigns_api_deploy"
SSH_KEY_PATH="$HOME/.ssh/$SSH_KEY_NAME"

# ================================================
# FUNÇÕES
# ================================================

# Função para criar ou atualizar .env.deploy
create_env_file() {
    log "Criando arquivo de configuração .env.deploy..."
    
    cat > "$ENV_FILE" << EOF
# ================================================
# Configurações de Deploy - i9 Smart Campaigns API
# ================================================
# Gerado em: $(date)
# ================================================

# Servidor SSH
export SSH_USER="$SSH_USER"
export SSH_HOST="$SSH_HOST"
export SSH_PORT="$SSH_PORT"
export SSH_KEY="$SSH_KEY_PATH"

# Informações do Projeto
export PROJECT_NAME="$PROJECT_NAME"
export REMOTE_DIR="/docker/i9-smart/campaigns_api"

# Configurações Docker
export CONTAINER_NAME="i9-campaigns-api"
export IMAGE_NAME="i9-campaigns-api"
export REDIS_CONTAINER="i9-campaigns-redis"

# Portas
export APP_PORT_HOMOLOG="8001"
export APP_PORT_PRODUCTION="8000"
export REDIS_PORT_HOMOLOG="6380"
export REDIS_PORT_PRODUCTION="6379"
EOF

    chmod 600 "$ENV_FILE"
    success "Arquivo .env.deploy criado"
}

# Função para adicionar ao .gitignore
update_gitignore() {
    if [ -f ".gitignore" ]; then
        if ! grep -q "^.env.deploy$" .gitignore; then
            log "Adicionando .env.deploy ao .gitignore..."
            echo -e "\n# Deploy configuration" >> .gitignore
            echo ".env.deploy" >> .gitignore
            echo "*.pem" >> .gitignore
            echo "*.key" >> .gitignore
            success ".gitignore atualizado"
        else
            log ".env.deploy já está no .gitignore"
        fi
    else
        warning ".gitignore não encontrado"
    fi
}

# Função para configurar SSH config
setup_ssh_config() {
    log "Configurando SSH config..."
    
    # Criar arquivo de config se não existir
    if [ ! -f "$SSH_CONFIG_FILE" ]; then
        touch "$SSH_CONFIG_FILE"
        chmod 600 "$SSH_CONFIG_FILE"
    fi
    
    # Verificar se já existe entrada para o projeto
    if grep -q "Host i9-campaigns-api" "$SSH_CONFIG_FILE"; then
        warning "Entrada SSH já existe para i9-campaigns-api, pulando..."
    else
        cat >> "$SSH_CONFIG_FILE" << EOF

# i9 Smart Campaigns API Deploy
Host i9-campaigns-api
    HostName $SSH_HOST
    User $SSH_USER
    Port $SSH_PORT
    IdentityFile $SSH_KEY_PATH
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
EOF
        success "SSH config atualizada"
    fi
}

# Função para criar aliases úteis
create_aliases() {
    log "Criando aliases úteis..."
    
    ALIAS_FILE="$HOME/.i9_campaigns_api_aliases"
    
    cat > "$ALIAS_FILE" << 'EOF'
# Aliases para i9 Smart Campaigns API
alias i9-api-ssh="ssh i9-campaigns-api"
alias i9-api-deploy-h="./deploy.sh homolog"
alias i9-api-deploy-p="./deploy.sh production"
alias i9-api-logs="ssh i9-campaigns-api 'docker logs -f i9-campaigns-api'"
alias i9-api-status="ssh i9-campaigns-api 'docker ps | grep i9-campaigns'"
alias i9-api-restart="ssh i9-campaigns-api 'docker restart i9-campaigns-api'"
alias i9-api-shell="ssh i9-campaigns-api 'docker exec -it i9-campaigns-api /bin/bash'"
alias i9-api-redis="ssh i9-campaigns-api 'docker exec -it i9-campaigns-redis redis-cli'"
EOF
    
    # Adicionar ao bashrc/zshrc se não estiver
    SHELL_RC="$HOME/.bashrc"
    if [ -f "$HOME/.zshrc" ]; then
        SHELL_RC="$HOME/.zshrc"
    fi
    
    if ! grep -q "i9_campaigns_api_aliases" "$SHELL_RC"; then
        echo "" >> "$SHELL_RC"
        echo "# i9 Smart Campaigns API Aliases" >> "$SHELL_RC"
        echo "[ -f $ALIAS_FILE ] && source $ALIAS_FILE" >> "$SHELL_RC"
        success "Aliases adicionados ao $SHELL_RC"
        echo -e "${YELLOW}Execute 'source $SHELL_RC' para carregar os aliases${NC}"
    fi
}

# ================================================
# EXECUÇÃO PRINCIPAL
# ================================================

# 1. Verificar se .env.deploy já existe
if [ -f "$ENV_FILE" ]; then
    warning "Arquivo .env.deploy já existe"
    read -p "Deseja reconfigurá-lo? (s/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        log "Mantendo configuração existente"
        source "$ENV_FILE"
        SSH_USER=${SSH_USER:-$DEFAULT_USER}
        SSH_HOST=${SSH_HOST:-$DEFAULT_HOST}
        SSH_PORT=${SSH_PORT:-$DEFAULT_PORT}
    else
        rm -f "$ENV_FILE"
    fi
fi

# 2. Coletar informações se necessário
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${MAGENTA}Configuração Inicial do Deploy${NC}"
    echo "--------------------------------"
    
    # Solicitar usuário SSH
    read -p "Digite o usuário SSH [$DEFAULT_USER]: " SSH_USER
    SSH_USER=${SSH_USER:-$DEFAULT_USER}
    
    # Solicitar host SSH
    read -p "Digite o host/IP do servidor [$DEFAULT_HOST]: " SSH_HOST
    SSH_HOST=${SSH_HOST:-$DEFAULT_HOST}
    
    # Solicitar porta SSH
    read -p "Digite a porta SSH [$DEFAULT_PORT]: " SSH_PORT
    SSH_PORT=${SSH_PORT:-$DEFAULT_PORT}
    
    echo ""
fi

# 3. Verificar/criar chave SSH
if [ -f "$SSH_KEY_PATH" ]; then
    success "Chave SSH já existe: $SSH_KEY_PATH"
else
    log "Gerando nova chave SSH..."
    ssh-keygen -t rsa -b 4096 -f "$SSH_KEY_PATH" -N "" -C "deploy@$PROJECT_NAME"
    success "Chave SSH gerada: $SSH_KEY_PATH"
fi

# 4. Copiar chave pública para o servidor
log "Copiando chave pública para o servidor..."
echo ""
echo -e "${YELLOW}ATENÇÃO: Você precisará digitar a senha SSH uma única vez${NC}"
echo ""

# Tentar copiar a chave
ssh-copy-id -i "$SSH_KEY_PATH.pub" -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" 2>/dev/null || {
    # Se falhar, tentar método alternativo
    warning "ssh-copy-id falhou, tentando método alternativo..."
    
    echo -e "${YELLOW}Digite a senha SSH para $SSH_USER@$SSH_HOST:${NC}"
    cat "$SSH_KEY_PATH.pub" | ssh -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" \
        "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
}

success "Chave pública copiada para o servidor"

# 5. Testar conexão sem senha
log "Testando conexão SSH sem senha..."
if ssh -i "$SSH_KEY_PATH" -p "$SSH_PORT" -o BatchMode=yes -o ConnectTimeout=5 \
    "$SSH_USER@$SSH_HOST" "echo 'Conexão SSH bem-sucedida!'" 2>/dev/null; then
    success "Conexão SSH configurada com sucesso!"
else
    error "Falha ao conectar via SSH. Verifique as configurações."
fi

# 6. Criar arquivo .env.deploy
create_env_file

# 7. Atualizar .gitignore
update_gitignore

# 8. Configurar SSH config
setup_ssh_config

# 9. Criar aliases
create_aliases

# 10. Verificar Docker no servidor
log "Verificando Docker no servidor remoto..."
if ssh -i "$SSH_KEY_PATH" -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "docker version" &>/dev/null; then
    success "Docker está instalado e acessível"
else
    warning "Docker não encontrado ou usuário sem permissão"
    echo -e "${YELLOW}Certifique-se de que:${NC}"
    echo "  1. Docker está instalado no servidor"
    echo "  2. Usuário $SSH_USER está no grupo docker"
    echo "  3. Execute no servidor: sudo usermod -aG docker $SSH_USER"
fi

# 11. Criar estrutura inicial no servidor
log "Criando estrutura de diretórios no servidor..."
ssh -i "$SSH_KEY_PATH" -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" \
    "mkdir -p /docker/i9-smart/campaigns_api/{app,migrations,static,repo,logs}"
success "Estrutura de diretórios criada"

# ================================================
# FINALIZAÇÃO
# ================================================

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}     Setup Concluído com Sucesso! 🎉          ${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${CYAN}Configurações Salvas:${NC}"
echo -e "  📁 Arquivo: ${YELLOW}$ENV_FILE${NC}"
echo -e "  🔑 Chave SSH: ${YELLOW}$SSH_KEY_PATH${NC}"
echo -e "  👤 Usuário: ${YELLOW}$SSH_USER${NC}"
echo -e "  🖥️  Servidor: ${YELLOW}$SSH_HOST:$SSH_PORT${NC}"
echo -e "  📂 Diretório Remoto: ${YELLOW}/docker/i9-smart/campaigns_api${NC}"
echo ""
echo -e "${CYAN}Próximos Passos:${NC}"
echo -e "  1. ${YELLOW}source ~/.bashrc${NC} (ou ~/.zshrc) para carregar aliases"
echo -e "  2. ${YELLOW}make deploy-homolog${NC} para fazer o primeiro deploy"
echo -e "  3. ${YELLOW}make deploy-status${NC} para verificar o status"
echo ""
echo -e "${CYAN}Aliases Disponíveis:${NC}"
echo -e "  ${YELLOW}i9-api-ssh${NC} - Conectar ao servidor"
echo -e "  ${YELLOW}i9-api-deploy-h${NC} - Deploy para homologação"
echo -e "  ${YELLOW}i9-api-deploy-p${NC} - Deploy para produção"
echo -e "  ${YELLOW}i9-api-logs${NC} - Ver logs em tempo real"
echo -e "  ${YELLOW}i9-api-status${NC} - Verificar status dos containers"
echo -e "  ${YELLOW}i9-api-restart${NC} - Reiniciar API"
echo -e "  ${YELLOW}i9-api-shell${NC} - Acessar shell do container"
echo -e "  ${YELLOW}i9-api-redis${NC} - Acessar Redis CLI"
echo ""

# Fazer scripts executáveis
chmod +x deploy.sh 2>/dev/null || true
chmod +x setup-ssh.sh 2>/dev/null || true

exit 0