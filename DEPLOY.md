# 🚀 Deploy - i9 Smart Feed API

Sistema unificado de deploy para a API FastAPI em múltiplos ambientes.

## 📋 Ambientes Disponíveis

### 🔧 Development (Local)
- **Comando**: `make deploy-development`
- **Descrição**: Executa `make dev` localmente
- **URL**: http://localhost:8000

### 🧪 Homologação
- **Servidor**: 10.0.20.11 (usuário: lee)
- **Comando**: `make deploy-homolog`
- **Porta**: 8001
- **URL**: http://10.0.20.11:8001

### 🏭 Produção
- **Servidor**: 172.16.2.90 (usuário: i9on)
- **Comando**: `make deploy-production`
- **Porta**: 8000
- **URL**: http://172.16.2.90:8000

## ⚙️ Configuração Inicial

### 1. Configurar SSH (executar uma vez)
```bash
make setup-ssh
```

Isto irá:
- Gerar chave SSH `id_rsa_i9_deploy` (se não existir)
- Configurar acesso aos servidores de homolog e produção
- Testar as conexões

### 2. Arquivos de Configuração

Os arquivos `.env.deploy.*` contêm as configurações específicas de cada ambiente:

- `.env.deploy.development` - Desenvolvimento local
- `.env.deploy.homolog` - Homologação
- `.env.deploy.production` - Produção

## 🚀 Como Fazer Deploy

### Desenvolvimento
```bash
make deploy-development
# ou
make dev
```

### Homologação
```bash
make deploy-homolog
```

### Produção
```bash
make deploy-production
```

**⚠️ Atenção**: Deploy para produção requer confirmação manual.

## 🐳 Processo de Deploy

### 1. Verificações
- Arquivos obrigatórios (Dockerfile, requirements.txt, etc.)
- Conexão SSH
- Estrutura de diretórios

### 2. Transferência
- Código da aplicação (`app/`)
- Migrações do banco (`migrations/`)
- Arquivos estáticos (`static/`, `repo/`)
- Configurações (Dockerfile, docker-compose.yml, etc.)

### 3. Build e Deploy
- Build da imagem Docker no servidor
- Parada dos containers antigos
- Execução das migrações do banco
- Início dos novos containers (API + Redis)

### 4. Verificações Finais
- Status dos containers
- Health check da API
- Logs iniciais

## 📊 Comandos de Monitoramento

```bash
# Verificar status dos containers
make deploy-status

# Ver logs da API
make deploy-logs

# Reiniciar containers
make deploy-restart

# Acessar shell do container
make deploy-shell

# SSH para o servidor
make deploy-ssh

# Informações de configuração
make deploy-info

# Limpeza de imagens antigas
make deploy-clean
```

## 📁 Estrutura no Servidor

```
/docker/i9-smart/feed-api/
├── app/                    # Código da aplicação
├── migrations/             # Migrações do banco
├── static/                 # Arquivos estáticos
├── repo/                   # Repositório de imagens
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── alembic.ini
└── .env                    # Variáveis de ambiente
```

## 🔒 Segurança

- **Chave SSH**: Única para todos os ambientes (`id_rsa_i9_deploy`)
- **Produção**: Comandos executados com `sudo` quando necessário
- **Confirmação**: Deploy para produção requer confirmação manual
- **Isolamento**: Cada ambiente usa portas diferentes

## 🌐 URLs de Acesso

### Homologação
- **API**: http://10.0.20.11:8001
- **Docs**: http://10.0.20.11:8001/docs
- **ReDoc**: http://10.0.20.11:8001/redoc
- **Health**: http://10.0.20.11:8001/health

### Produção
- **API**: http://172.16.2.90:8000
- **Docs**: http://172.16.2.90:8000/docs
- **ReDoc**: http://172.16.2.90:8000/redoc
- **Health**: http://172.16.2.90:8000/health

## 🚨 Solução de Problemas

### Deploy Falha
1. Verificar conexão SSH: `make deploy-ssh`
2. Verificar logs: `make deploy-logs`
3. Verificar status: `make deploy-status`

### Containers Não Iniciam
1. Verificar logs: `make deploy-logs`
2. Verificar configuração: `make deploy-info`
3. Reiniciar: `make deploy-restart`

### Permissões SSH
1. Reconfigurar SSH: `make setup-ssh`
2. Verificar chave: `ls -la ~/.ssh/id_rsa_i9_deploy*`

## 📝 Logs e Debug

### Ver Logs em Tempo Real
```bash
make deploy-logs
```

### Acessar Container
```bash
make deploy-shell
```

### SSH para Servidor
```bash
make deploy-ssh
```

## 🔄 Rollback

Para fazer rollback, você pode:

1. **Usar imagem anterior** (se disponível):
```bash
# No servidor
docker run -d --name i9-feed-api -p 8001:8000 --env-file .env i9-feed-api:previous
```

2. **Deploy de versão anterior**:
```bash
git checkout <commit-anterior>
make deploy-homolog  # Testar primeiro
make deploy-production  # Se OK
```

## 🏷️ Versionamento

O sistema usa tags baseadas no ambiente:
- `i9-feed-api:homolog` - Versão de homologação
- `i9-feed-api:production` - Versão de produção

## 📞 Suporte

Em caso de problemas:
1. Verificar este documento
2. Executar comandos de diagnóstico
3. Contatar: Lee Chardes

---

**Última atualização**: 30/09/2025