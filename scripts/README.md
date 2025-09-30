# 📁 Scripts - i9 Smart Feed API

Esta pasta contém todos os scripts de automação do projeto.

## 🚀 Scripts Disponíveis

### deploy.sh
Script unificado para deploy em todos os ambientes.

**Uso:**
```bash
# Desenvolvimento
./scripts/deploy.sh development

# Homologação
./scripts/deploy.sh homolog

# Produção
./scripts/deploy.sh production
```

**Funcionalidades:**
- Build automático da imagem Docker
- Deploy via Docker containers
- Suporte a múltiplos ambientes
- Execução de migrações de banco
- Confirmação de segurança para produção

### setup-ssh.sh
Configura chave SSH para acesso aos servidores.

**Uso:**
```bash
./scripts/setup-ssh.sh
```

**Funcionalidades:**
- Gera chave SSH (se não existir)
- Configura acesso para homologação e produção
- Atualiza arquivo SSH config
- Testa conexões

## 🔧 Scripts de Desenvolvimento

### Banco de Dados
- `clean_database.py` - Limpa banco de dados
- `create_admin_user.py` - Cria usuário administrador
- `create_test_user.py` - Cria usuário de teste
- `reset_admin_password.py` - Reset senha do admin
- `seed_data.py` - Dados iniciais

### Dados de Teste
- `add_branches_test_data.py` - Adiciona filiais de teste
- `add_realistic_branches_data.py` - Dados realistas de filiais

### Imagens
- `gen_repo_images.py` - Gera imagens de teste
- `bulk_import_repo_images.py` - Importa imagens em lote

### Integração
- `test_sync.py` - Testa sincronização
- `export_openapi.py` - Exporta documentação da API

## 🔧 Configuração

Os scripts utilizam arquivos de ambiente localizados na raiz do projeto:
- `.env.deploy.development` - Configurações de desenvolvimento
- `.env.deploy.homolog` - Configurações de homologação
- `.env.deploy.production` - Configurações de produção

## 📋 Pré-requisitos

- Python 3.11+ com ambiente virtual
- Docker instalado nos servidores
- SSH configurado
- Permissões de acesso aos servidores

## 🎯 Uso via Makefile

Todos os scripts podem ser executados através do Makefile:

```bash
# Deploy
make deploy-development
make deploy-homolog
make deploy-production

# Configuração SSH
make setup-ssh

# Monitoramento
make deploy-status
make deploy-logs
make deploy-restart
```

## ⚠️ Importante

- Sempre teste em homologação antes de produção
- Faça backup antes de deploy em produção
- Mantenha as credenciais seguras
- Não commitar arquivos `.env`

## 📞 Suporte

Em caso de problemas, contate: Lee Chardes