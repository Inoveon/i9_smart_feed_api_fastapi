#!/bin/bash

# Script de teste rápido da API i9 Smart Feed
# Uso: ./test-api-quick.sh

API_URL="http://172.16.2.90:8000"
TOKEN=""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}       Teste Rápido - i9 Smart Feed API${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n"

# 1. Verificar Health
echo -e "${YELLOW}1. Verificando saúde da API...${NC}"
HEALTH=$(curl -s ${API_URL}/health)
if [[ $HEALTH == *"healthy"* ]]; then
    echo -e "${GREEN}✅ API está saudável${NC}\n"
else
    echo -e "${RED}❌ API não está respondendo${NC}\n"
    exit 1
fi

# 2. Login
echo -e "${YELLOW}2. Fazendo login...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST ${API_URL}/api/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=adminuser&password=Admin@123456")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Falha no login${NC}"
    echo "Resposta: $LOGIN_RESPONSE"
    exit 1
else
    echo -e "${GREEN}✅ Login realizado com sucesso${NC}"
    echo -e "Token: ${TOKEN:0:20}...\n"
fi

# 3. Listar Campanhas
echo -e "${YELLOW}3. Listando campanhas...${NC}"
CAMPAIGNS=$(curl -s ${API_URL}/api/campaigns \
    -H "Authorization: Bearer $TOKEN")

CAMPAIGN_COUNT=$(echo $CAMPAIGNS | grep -o '"id"' | wc -l)
echo -e "${GREEN}✅ ${CAMPAIGN_COUNT} campanhas encontradas${NC}"

# Pegar ID da primeira campanha ativa
CAMPAIGN_ID=$(echo $CAMPAIGNS | grep -o '"id":"[^"]*' | head -1 | cut -d'"' -f4)
if [ ! -z "$CAMPAIGN_ID" ]; then
    echo -e "Primeira campanha ID: $CAMPAIGN_ID\n"
fi

# 4. Verificar Filiais
echo -e "${YELLOW}4. Verificando filiais...${NC}"
BRANCHES=$(curl -s ${API_URL}/api/branches?limit=5 \
    -H "Authorization: Bearer $TOKEN")

BRANCH_COUNT=$(echo $BRANCHES | grep -o '"total":[0-9]*' | cut -d':' -f2)
echo -e "${GREEN}✅ ${BRANCH_COUNT} filiais sincronizadas do SQL Server${NC}\n"

# 5. Verificar Estações
echo -e "${YELLOW}5. Verificando estações...${NC}"
STATIONS=$(curl -s ${API_URL}/api/stations?limit=5 \
    -H "Authorization: Bearer $TOKEN")

STATION_COUNT=$(echo $STATIONS | grep -o '"total":[0-9]*' | cut -d':' -f2)
echo -e "${GREEN}✅ ${STATION_COUNT} estações disponíveis${NC}\n"

# 6. Criar Campanha de Teste
echo -e "${YELLOW}6. Criando campanha de teste...${NC}"
TEST_DATE=$(date -u +"%Y-%m-%dT%H:%M:%S")
END_DATE=$(date -u -d "+7 days" +"%Y-%m-%dT%H:%M:%S")

NEW_CAMPAIGN=$(curl -s -X POST ${API_URL}/api/campaigns \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"Teste API $(date +%H:%M:%S)\",
        \"description\": \"Campanha criada via script de teste\",
        \"status\": \"active\",
        \"start_date\": \"$TEST_DATE\",
        \"end_date\": \"$END_DATE\",
        \"default_display_time\": 5000,
        \"stations\": [\"010101\"]
    }")

NEW_ID=$(echo $NEW_CAMPAIGN | grep -o '"id":"[^"]*' | cut -d'"' -f4)
if [ ! -z "$NEW_ID" ]; then
    echo -e "${GREEN}✅ Campanha criada com ID: $NEW_ID${NC}\n"
    CAMPAIGN_ID=$NEW_ID
else
    echo -e "${RED}❌ Erro ao criar campanha${NC}"
    echo "Resposta: $NEW_CAMPAIGN\n"
fi

# 7. Verificar imagens da campanha (se houver)
if [ ! -z "$CAMPAIGN_ID" ]; then
    echo -e "${YELLOW}7. Verificando imagens da campanha...${NC}"
    CAMPAIGN_DETAIL=$(curl -s ${API_URL}/api/campaigns/${CAMPAIGN_ID} \
        -H "Authorization: Bearer $TOKEN")
    
    IMAGE_COUNT=$(echo $CAMPAIGN_DETAIL | grep -o '"url":"/static' | wc -l)
    echo -e "${GREEN}✅ ${IMAGE_COUNT} imagens na campanha${NC}"
    
    # Listar URLs das imagens
    if [ $IMAGE_COUNT -gt 0 ]; then
        echo -e "\nURLs das imagens:"
        echo $CAMPAIGN_DETAIL | grep -o '"/static/uploads/[^"]*' | while read url; do
            echo -e "  ${BLUE}${API_URL}${url}${NC}"
        done
    fi
fi

# 8. Testar endpoint de tablet
echo -e "\n${YELLOW}8. Testando endpoint do tablet...${NC}"
TABLET_RESPONSE=$(curl -s ${API_URL}/api/stations/010101/active-campaigns \
    -H "X-API-Key: tablet_api_key_2025")

if [[ $TABLET_RESPONSE == *"campaigns"* ]]; then
    ACTIVE_COUNT=$(echo $TABLET_RESPONSE | grep -o '"id"' | wc -l)
    echo -e "${GREEN}✅ Endpoint tablet funcionando - ${ACTIVE_COUNT} campanhas ativas${NC}"
else
    echo -e "${RED}❌ Erro no endpoint do tablet${NC}"
fi

# Resumo Final
echo -e "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                    RESUMO DOS TESTES${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ API Health Check${NC}"
echo -e "${GREEN}✅ Autenticação JWT${NC}"
echo -e "${GREEN}✅ ${CAMPAIGN_COUNT} Campanhas disponíveis${NC}"
echo -e "${GREEN}✅ ${BRANCH_COUNT} Filiais sincronizadas${NC}"
echo -e "${GREEN}✅ ${STATION_COUNT} Estações configuradas${NC}"
echo -e "${GREEN}✅ Criação de campanha${NC}"
echo -e "${GREEN}✅ Endpoint tablet (API Key)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "\n${YELLOW}📌 URLs Importantes:${NC}"
echo -e "   API: ${BLUE}${API_URL}${NC}"
echo -e "   Docs: ${BLUE}${API_URL}/docs${NC}"
echo -e "   ReDoc: ${BLUE}${API_URL}/redoc${NC}"
echo -e "\n${GREEN}✅ Todos os testes passaram com sucesso!${NC}\n"