#!/bin/bash

# Setup SSH para ambientes i9 Smart Feed Portal
# Uso: ./setup-ssh.sh [homolog|production|all]

set -e  # Para o script se houver erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Determinar ambiente
ENV="${1:-all}"

# Validar ambiente
if [ "$ENV" != "homolog" ] && [ "$ENV" != "production" ] && [ "$ENV" != "all" ]; then
    echo -e "${RED}❌ Ambiente inválido: $ENV${NC}"
    echo -e "${YELLOW}Uso: $0 [homolog|production|all]${NC}"
    echo ""
    echo -e "${BLUE}Opções:${NC}"
    echo "  homolog    - Configura apenas homologação"
    echo "  production - Configura apenas produção"
    echo "  all        - Configura todos os ambientes (padrão)"
    exit 1
fi

echo -e "${GREEN}🔐 Configuração de SSH - i9 Smart Feed Portal${NC}"
echo -e "${BLUE}Ambiente: ${ENV}${NC}"
echo ""

# Configurações da chave SSH
SSH_KEY_NAME="id_rsa_i9_deploy"
SSH_KEY_PATH="$HOME/.ssh/$SSH_KEY_NAME"

# Configurações dos servidores
HOMOLOG_HOST="10.0.20.11"
HOMOLOG_USER="lee"

PRODUCTION_HOST="172.16.2.90"
PRODUCTION_USER="i9on"
PRODUCTION_PASS='aldo$2024'

# 1. Verificar/Criar chave SSH
if [ -f "$SSH_KEY_PATH" ]; then
    echo -e "${GREEN}✅ Chave SSH já existe em: $SSH_KEY_PATH${NC}"
    echo -e "${BLUE}Usando chave existente${NC}"
else
    echo -e "${YELLOW}🔑 Gerando nova chave SSH...${NC}"
    ssh-keygen -t rsa -b 4096 -f "$SSH_KEY_PATH" -N "" -C "i9-smart-deploy"
    echo -e "${GREEN}✅ Chave SSH gerada em: $SSH_KEY_PATH${NC}"
fi

# 2. Adicionar chave ao ssh-agent
echo -e "${YELLOW}🔐 Adicionando chave ao ssh-agent...${NC}"
eval "$(ssh-agent -s)" > /dev/null 2>&1
ssh-add "$SSH_KEY_PATH" 2>/dev/null
echo -e "${GREEN}✅ Chave adicionada ao ssh-agent${NC}"

# 3. Configurar SSH config
echo -e "${YELLOW}⚙️  Configurando SSH config...${NC}"
SSH_CONFIG="$HOME/.ssh/config"

# Backup do config existente
if [ -f "$SSH_CONFIG" ]; then
    cp "$SSH_CONFIG" "$SSH_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Remover configurações antigas se existirem
sed -i.tmp '/# i9 Smart Feed Portal - Start/,/# i9 Smart Feed Portal - End/d' "$SSH_CONFIG" 2>/dev/null || true

# Função para adicionar host ao SSH config
add_ssh_host() {
    local host_alias=$1
    local host_ip=$2
    local host_user=$3
    
    cat >> "$SSH_CONFIG" << EOF

Host $host_alias
    HostName $host_ip
    User $host_user
    IdentityFile $SSH_KEY_PATH
    StrictHostKeyChecking no
    ServerAliveInterval 60
    ServerAliveCountMax 3
EOF
}

# Adicionar configurações baseado no ambiente escolhido
echo "" >> "$SSH_CONFIG"
echo "# i9 Smart Feed Portal - Start" >> "$SSH_CONFIG"

if [ "$ENV" = "homolog" ] || [ "$ENV" = "all" ]; then
    add_ssh_host "i9-homolog" "$HOMOLOG_HOST" "$HOMOLOG_USER"
    echo -e "${GREEN}✅ Configuração para homologação adicionada${NC}"
fi

if [ "$ENV" = "production" ] || [ "$ENV" = "all" ]; then
    add_ssh_host "i9-production" "$PRODUCTION_HOST" "$PRODUCTION_USER"
    echo -e "${GREEN}✅ Configuração para produção adicionada${NC}"
fi

echo "# i9 Smart Feed Portal - End" >> "$SSH_CONFIG"

# 4. Copiar chave pública para os servidores
echo ""

# Função para configurar servidor
setup_server() {
    local server_name=$1
    local server_host=$2
    local server_user=$3
    local server_pass=$4
    
    echo -e "${YELLOW}📤 Configurando servidor de ${server_name} (${server_host})...${NC}"
    
    if [ -n "$server_pass" ]; then
        # Produção com senha
        if command -v sshpass &> /dev/null; then
            sshpass -p "$server_pass" ssh-copy-id -i "$SSH_KEY_PATH.pub" \
                -o StrictHostKeyChecking=no "$server_user@$server_host" 2>/dev/null
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ Chave configurada para ${server_name}${NC}"
            else
                echo -e "${YELLOW}⚠️  Tentando método alternativo...${NC}"
                echo "$server_pass" | ssh "$server_user@$server_host" \
                    "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys" < "$SSH_KEY_PATH.pub"
            fi
        else
            echo -e "${YELLOW}Digite a senha quando solicitado: ${server_pass}${NC}"
            ssh-copy-id -i "$SSH_KEY_PATH.pub" "$server_user@$server_host"
        fi
    else
        # Homologação sem senha automática
        echo -e "${BLUE}Digite a senha para o usuário $server_user quando solicitado:${NC}"
        ssh-copy-id -i "$SSH_KEY_PATH.pub" "$server_user@$server_host" 2>/dev/null || \
            echo -e "${YELLOW}⚠️  Pule se já estiver configurado${NC}"
    fi
}

# Configurar servidores baseado no ambiente
if [ "$ENV" = "homolog" ] || [ "$ENV" = "all" ]; then
    setup_server "HOMOLOGAÇÃO" "$HOMOLOG_HOST" "$HOMOLOG_USER" ""
fi

if [ "$ENV" = "production" ] || [ "$ENV" = "all" ]; then
    setup_server "PRODUÇÃO" "$PRODUCTION_HOST" "$PRODUCTION_USER" "$PRODUCTION_PASS"
fi

# 5. Testar conexões
echo ""
echo -e "${YELLOW}🧪 Testando conexões...${NC}"

if [ "$ENV" = "homolog" ] || [ "$ENV" = "all" ]; then
    echo -e "${BLUE}Homologação:${NC}"
    ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=5 "$HOMOLOG_USER@$HOMOLOG_HOST" \
        "echo '  ✅ Conexão OK'" 2>/dev/null || echo "  ❌ Falha na conexão"
fi

if [ "$ENV" = "production" ] || [ "$ENV" = "all" ]; then
    echo -e "${BLUE}Produção:${NC}"
    ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=5 "$PRODUCTION_USER@$PRODUCTION_HOST" \
        "echo '  ✅ Conexão OK'" 2>/dev/null || echo "  ❌ Falha na conexão"
fi

# 6. Resumo
echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}🎉 Configuração Concluída!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "${BLUE}📋 Resumo:${NC}"
echo -e "   ${YELLOW}Chave SSH:${NC} $SSH_KEY_PATH"
echo -e "   ${YELLOW}Ambiente(s):${NC} $ENV"
echo ""

if [ "$ENV" = "homolog" ] || [ "$ENV" = "all" ]; then
    echo -e "${BLUE}📡 Homologação:${NC}"
    echo -e "   • Host: $HOMOLOG_HOST"
    echo -e "   • User: $HOMOLOG_USER"
    echo -e "   • Alias: ssh i9-homolog"
    echo ""
fi

if [ "$ENV" = "production" ] || [ "$ENV" = "all" ]; then
    echo -e "${BLUE}📡 Produção:${NC}"
    echo -e "   • Host: $PRODUCTION_HOST"
    echo -e "   • User: $PRODUCTION_USER"
    echo -e "   • Alias: ssh i9-production"
    echo ""
fi

echo -e "${BLUE}🚀 Comandos de Deploy:${NC}"
if [ "$ENV" = "homolog" ] || [ "$ENV" = "all" ]; then
    echo -e "   ${YELLOW}Homologação:${NC} make deploy-homolog"
fi
if [ "$ENV" = "production" ] || [ "$ENV" = "all" ]; then
    echo -e "   ${YELLOW}Produção:${NC}    make deploy-production"
fi

echo ""
echo -e "${BLUE}💡 Dicas:${NC}"
echo "• Use os aliases para conectar diretamente:"
if [ "$ENV" = "homolog" ] || [ "$ENV" = "all" ]; then
    echo "    ssh i9-homolog"
fi
if [ "$ENV" = "production" ] || [ "$ENV" = "all" ]; then
    echo "    ssh i9-production"
fi
echo "• Para configurar outro ambiente: $0 [homolog|production|all]"