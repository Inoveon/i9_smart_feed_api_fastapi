# 🚀 Sistema Completo de Deploy com Docker

## 📚 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Estrutura de Arquivos](#estrutura-de-arquivos)
4. [Configuração Inicial](#configuração-inicial)
5. [Scripts de Automação](#scripts-de-automação)
6. [Makefile - Comandos](#makefile---comandos)
7. [Docker](#docker)
8. [Fluxo de Deploy](#fluxo-de-deploy)
9. [Segurança](#segurança)
10. [Troubleshooting](#troubleshooting)
11. [Template para Outros Projetos](#template-para-outros-projetos)

## Visão Geral

Sistema automatizado de deploy que permite fazer build local, transferir arquivos via SCP e executar containers Docker em servidor remoto, sem necessidade de Docker local.

### Características Principais

- ✅ **Sem Docker local necessário** - Build acontece no servidor
- ✅ **Autenticação segura** - Via chave SSH
- ✅ **Zero downtime** - Container novo substitui o antigo
- ✅ **Multi-ambiente** - Homologação e Produção
- ✅ **Automação completa** - Um comando para deploy

## Arquitetura

```
┌─────────────────────┐
│   Desenvolvedor     │
│   (Local Machine)   │
│                     │
│  ▪ npm run build   │
│  ▪ ./deploy.sh     │
└──────────┬──────────┘
           │
           │ SSH + SCP
           │
           ▼
┌─────────────────────┐
│   Servidor Docker   │
│   (10.0.20.11)     │
│                     │
│  /docker/i9-smart/  │
│     └── campaigns/ │
│         ├── dist/   │
│         ├── Docker* │
│         └── nginx* │
└──────────┬──────────┘
           │
           │ docker build
           │ docker run
           ▼
┌─────────────────────┐
│   Container Nginx   │
│   (i9-campaigns)    │
│                     │
│   Port: 3001:80    │
│   Serve: SPA React │
└─────────────────────┘
```

## Estrutura de Arquivos

### 📁 Local (Projeto)

```
projeto/
├── src/                    # Código fonte React/Vite
├── dist/                   # Build do projeto (gerado)
├── .env.deploy            # Variáveis de ambiente (não commitado)
├── .gitignore             # Inclui .env.deploy
├── Dockerfile             # Imagem Docker (nginx:alpine)
├── docker-compose.yml     # Configuração do container
├── nginx.conf             # Configuração do Nginx
├── .dockerignore          # Arquivos ignorados no build
├── setup-ssh.sh           # Script configuração SSH
├── deploy.sh              # Script principal de deploy
└── Makefile               # Comandos automatizados
```

### 📁 Servidor Remoto

```
/docker/
└── i9-smart/
    └── campaigns/
        ├── dist/              # Frontend buildado
        ├── Dockerfile         # Definição da imagem
        ├── docker-compose.yml # Orquestração
        ├── nginx.conf         # Config do servidor web
        └── .dockerignore      # Exclusões do build
```

## Configuração Inicial

### 1️⃣ Primeira Execução - Setup SSH

```bash
# Executar uma única vez para configurar autenticação
make setup-ssh

# Ou diretamente
./setup-ssh.sh
```

**O que acontece:**
1. Pede usuário e senha SSH (senha só na primeira vez)
2. Gera chave SSH dedicada: `~/.ssh/id_rsa_i9_deploy`
3. Copia chave pública para o servidor
4. Cria arquivo `.env.deploy` com configurações
5. Adiciona entrada no `~/.ssh/config`
6. Testa conexão sem senha

### 2️⃣ Arquivo `.env.deploy` (Gerado Automaticamente)

```bash
# Configurações de Deploy
export SSH_USER="lee"
export SSH_HOST="10.0.20.11"
export SSH_KEY="/Users/seu-usuario/.ssh/id_rsa_i9_deploy"
```

## Scripts de Automação

### 📄 setup-ssh.sh

**Função:** Configuração inicial de autenticação SSH

```bash
#!/bin/bash
# Principais funções:
# 1. Configurar variável SSH_USER
# 2. Gerar chave SSH se não existir
# 3. Copiar chave para servidor
# 4. Testar conexão
# 5. Criar aliases úteis

# Uso:
./setup-ssh.sh
```

**Fluxo:**
1. Verifica/cria `.env.deploy`
2. Pede credenciais
3. Gera chave SSH RSA 4096 bits
4. Adiciona ao `authorized_keys` do servidor
5. Configura `~/.ssh/config`
6. Cria aliases no shell

### 📄 deploy.sh

**Função:** Script principal que executa todo o deploy

```bash
#!/bin/bash
# Parâmetros:
# $1 - Ambiente (homolog|production)

# Principais etapas:
# 1. npm run build local
# 2. Criar diretórios no servidor
# 3. Transferir arquivos via SCP
# 4. Build Docker no servidor
# 5. Substituir container antigo
# 6. Verificar status

# Uso:
./deploy.sh homolog
./deploy.sh production
```

**Etapas Detalhadas:**

```bash
# 1. Build Local
npm run build
# Gera pasta dist/ com arquivos estáticos

# 2. Criar Estrutura Remota
ssh user@server "mkdir -p /docker/i9-smart/campaigns"

# 3. Transferir Arquivos
scp -r dist Dockerfile nginx.conf docker-compose.yml user@server:/path/

# 4. Build Docker Remoto
ssh user@server "cd /path && docker build -t i9-campaigns:homolog ."

# 5. Recreate Container
docker stop i9-campaigns-frontend
docker rm i9-campaigns-frontend
docker run -d --name i9-campaigns-frontend \
  -p 3001:80 \
  --restart unless-stopped \
  i9-campaigns:homolog

# 6. Verificação
docker ps | grep i9-campaigns
docker logs i9-campaigns-frontend
```

## Makefile - Comandos

### 🛠️ Desenvolvimento

```makefile
make dev          # Inicia servidor dev (porta 5173)
make build        # Build de produção
make lint         # Verifica código
make type-check   # Verifica tipos TypeScript
make format       # Formata código
```

### 🚀 Deploy

```makefile
make setup-ssh         # Configura autenticação SSH (primeira vez)
make deploy-homolog    # Deploy para homologação
make deploy-production # Deploy para produção
make deploy-status     # Verifica se container está rodando
make deploy-logs       # Mostra logs do container
make deploy-restart    # Reinicia container
make deploy-ssh        # Conecta ao servidor via SSH
make deploy-info       # Mostra configuração atual
```

### 📦 Gestão

```makefile
make install          # Instala dependências
make clean            # Limpa arquivos temporários
make audit            # Verifica vulnerabilidades
make add-component    # Adiciona componente Shadcn/UI
```

## Docker

### 📄 Dockerfile

```dockerfile
# Imagem mínima com Nginx Alpine
FROM nginx:alpine

# Copiar build do React
COPY dist /usr/share/nginx/html

# Configuração customizada do Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expor porta 80
EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Comando padrão
CMD ["nginx", "-g", "daemon off;"]
```

**Características:**
- Base: `nginx:alpine` (mínima ~8MB)
- Serve arquivos estáticos do React
- Healthcheck integrado
- Configuração otimizada

### 📄 nginx.conf

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/javascript application/json;

    # Cache Control para assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Desabilitar cache para index.html
    location = /index.html {
        expires -1;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # React Router - SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

**Otimizações:**
- Compressão Gzip
- Cache agressivo para assets
- No-cache para index.html
- Suporte a React Router
- Headers de segurança

### 📄 docker-compose.yml

```yaml
services:
  i9-campaigns:
    image: i9-campaigns:${VERSION:-homolog}
    container_name: i9-campaigns-frontend
    restart: unless-stopped
    ports:
      - "${PORT:-3001}:80"
    environment:
      - TZ=America/Sao_Paulo
    labels:
      - "com.inoveon.project=i9-smart"
      - "com.inoveon.component=frontend"
      - "com.inoveon.version=${VERSION:-homolog}"
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 📄 .dockerignore

```
node_modules
npm-debug.log
.git
.gitignore
README.md
.env
.env.local
.vscode
.idea
.DS_Store
*.log
.eslintcache
coverage
src
public
docs
scripts
```

## Fluxo de Deploy

### 1️⃣ Setup Inicial (Uma vez)

```bash
# 1. Clone o projeto
git clone repo

# 2. Instale dependências
make install

# 3. Configure SSH
make setup-ssh
# Digite usuário: lee
# Digite senha: ******

# 4. Teste conexão
make deploy-ssh
```

### 2️⃣ Desenvolvimento

```bash
# 1. Desenvolvimento local
make dev

# 2. Verificar qualidade
make lint
make type-check

# 3. Build teste
make build
```

### 3️⃣ Deploy Homologação

```bash
# Deploy completo
make deploy-homolog

# Verificar status
make deploy-status

# Ver logs
make deploy-logs

# URL: http://10.0.20.11:3001
```

### 4️⃣ Deploy Produção

```bash
# Deploy para produção
make deploy-production

# Opcional: Push para registry
# O script perguntará se deseja fazer push
```

### 5️⃣ Rollback

```bash
# Conectar ao servidor
make deploy-ssh

# Listar imagens anteriores
docker images | grep i9-campaigns

# Voltar para versão anterior
docker stop i9-campaigns-frontend
docker run -d --name i9-campaigns-frontend \
  -p 3001:80 \
  i9-campaigns:previous-tag
```

## Segurança

### 🔐 Boas Práticas Implementadas

1. **Autenticação SSH por Chave**
   - Sem senhas em scripts
   - Chave dedicada para deploy
   - 4096 bits RSA

2. **Variáveis de Ambiente**
   - `.env.deploy` não commitado
   - Variáveis carregadas dinamicamente
   - Sem hardcode de credenciais

3. **Docker Security**
   - Imagem Alpine mínima
   - Usuário não-root no nginx
   - Healthchecks configurados
   - Security headers no nginx

4. **Rede**
   - SSH com StrictHostKeyChecking
   - Portas específicas
   - Firewall no servidor

### 🚫 O que Nunca Fazer

```bash
# NUNCA commitar:
- .env.deploy
- Chaves SSH privadas
- Senhas em scripts
- IPs de produção em público

# NUNCA executar:
- docker run sem --restart
- deploy sem testar build
- rm -rf sem verificar
```

## Troubleshooting

### ❌ Erro: "Permission denied"

```bash
# Verificar permissões da chave
chmod 600 ~/.ssh/id_rsa_i9_deploy

# Reconfigurar SSH
make setup-ssh
```

### ❌ Erro: "Container não inicia"

```bash
# Ver logs detalhados
make deploy-ssh
docker logs i9-campaigns-frontend -f

# Verificar portas em uso
lsof -i :3001
```

### ❌ Erro: "Build failed"

```bash
# Limpar e rebuildar
make clean
make install
make build

# Verificar espaço em disco no servidor
make deploy-ssh
df -h
```

### ❌ Erro: "Cannot connect to Docker"

```bash
# Verificar Docker no servidor
make deploy-ssh
docker version
sudo systemctl status docker
```

## Template para Outros Projetos

### 📋 Checklist de Adaptação

Para usar este sistema em outro projeto, ajuste:

#### 1. Variáveis no `deploy.sh`:

```bash
# Configurações específicas do projeto
REMOTE_DIR="/docker/seu-projeto/seu-app"  # Caminho no servidor
IMAGE_NAME="seu-app"                       # Nome da imagem Docker
CONTAINER_NAME="seu-app-frontend"          # Nome do container
PORT="${PORT:-3000}"                       # Porta do serviço
```

#### 2. Labels no `docker-compose.yml`:

```yaml
labels:
  - "com.suaempresa.project=seu-projeto"
  - "com.suaempresa.component=frontend"
  - "com.suaempresa.version=${VERSION:-homolog}"
```

#### 3. Configuração do `nginx.conf`:

```nginx
# Ajustar se necessário:
- Rotas da API
- Proxy reverso
- Domínios
- Certificados SSL
```

#### 4. Scripts do `package.json`:

```json
{
  "scripts": {
    "build": "seu-build-command",
    "dev": "seu-dev-command"
  }
}
```

#### 5. Servidor no `setup-ssh.sh`:

```bash
SERVER_HOST="seu.servidor.ip"
SSH_KEY_PATH="$HOME/.ssh/id_rsa_seu_projeto"
```

### 🎯 Estrutura Mínima Necessária

```bash
# Arquivos obrigatórios:
projeto/
├── package.json       # Com script "build"
├── Dockerfile         # Copiar template
├── nginx.conf         # Ajustar se necessário
├── docker-compose.yml # Ajustar nomes
├── .dockerignore      # Copiar template
├── setup-ssh.sh       # Copiar e ajustar IP
├── deploy.sh          # Copiar e ajustar variáveis
└── Makefile           # Copiar comandos úteis
```

### 🚀 Comando de Inicialização Rápida

```bash
# Para novo projeto, execute em ordem:
curl -O https://raw.githubusercontent.com/seu-repo/templates/main/setup-ssh.sh
curl -O https://raw.githubusercontent.com/seu-repo/templates/main/deploy.sh
curl -O https://raw.githubusercontent.com/seu-repo/templates/main/Dockerfile
curl -O https://raw.githubusercontent.com/seu-repo/templates/main/nginx.conf
curl -O https://raw.githubusercontent.com/seu-repo/templates/main/docker-compose.yml
curl -O https://raw.githubusercontent.com/seu-repo/templates/main/Makefile

# Ajustar variáveis
vim deploy.sh  # Editar REMOTE_DIR, IMAGE_NAME, etc
vim setup-ssh.sh  # Editar SERVER_HOST

# Configurar e deployar
make setup-ssh
make deploy-homolog
```

## 📊 Métricas e Monitoramento

### Comandos Úteis

```bash
# Status geral
make deploy-status

# Logs em tempo real
make deploy-ssh
docker logs -f i9-campaigns-frontend

# Recursos consumidos
docker stats i9-campaigns-frontend

# Espaço em disco
df -h /docker

# Verificar portas
netstat -tlpn | grep 3001
```

### Monitoramento Sugerido

1. **Healthchecks Docker**
   - Configurado no docker-compose.yml
   - Verifica a cada 30s
   - Reinicia se falhar 3x

2. **Logs Centralizados**
   ```bash
   # Configurar driver de logs
   docker run --log-driver=syslog
   ```

3. **Alertas**
   - Container parado
   - Uso de CPU > 80%
   - Uso de memória > 80%
   - Disco > 90%

## 📝 Notas Finais

### Vantagens do Sistema

✅ **Simplicidade** - Um comando para deploy completo
✅ **Segurança** - Sem senhas expostas
✅ **Flexibilidade** - Fácil adaptar para outros projetos
✅ **Eficiência** - Build otimizado, imagem mínima
✅ **Manutenibilidade** - Scripts organizados e documentados

### Evolução Futura

- [ ] CI/CD com GitHub Actions
- [ ] Deploy automático em push para main
- [ ] Testes automáticos antes do deploy
- [ ] Blue-Green deployment
- [ ] Backup automático antes do deploy
- [ ] Notificações Slack/Discord
- [ ] Métricas com Prometheus/Grafana

### Comandos Rápidos

```bash
# Deploy rápido
alias deploy-h="make deploy-homolog"
alias deploy-p="make deploy-production"
alias deploy-log="make deploy-logs"
alias deploy-stat="make deploy-status"
```

---

**Última atualização:** Janeiro 2025
**Autor:** Sistema de Deploy i9 Smart
**Versão:** 1.0.0

> 💡 **Dica:** Mantenha este documento atualizado conforme o sistema evolui!