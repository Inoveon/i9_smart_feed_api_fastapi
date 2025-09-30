# 🚀 Melhorias de Deploy - i9 Smart Feed API

## 📋 Resumo das Melhorias

Esta documentação descreve as melhorias implementadas no sistema de deploy para **proteger dados dos usuários** e garantir **deploys seguros** sem interferir com conteúdo existente.

---

## 🎯 Problemas Resolvidos

### ❌ **Problemas Anteriores:**
1. **Banco de dados**: Script tentava criar estrutura sempre
2. **Pasta static/**: Deploy sobrescrevia uploads dos usuários
3. **Sem backup**: Deploys sem proteção de dados críticos
4. **Volumes**: Dados não persistiam entre deploys

### ✅ **Soluções Implementadas:**
1. **Verificação inteligente de banco**: Detecta estado e aplica apenas migrações necessárias
2. **Proteção de dados**: Static/ nunca é sobrescrito no deploy
3. **Backup automático**: Backup antes de deploys críticos
4. **Volumes persistentes**: Dados preservados entre deploys

---

## 🛠️ Novos Arquivos Criados

### 1. `scripts/check_database.py`
**Função**: Verifica estado do banco de dados antes de aplicar migrações

```python
# Retorna:
# - PRIMEIRA_INSTALACAO: Banco existe mas sem estrutura
# - MIGRACOES_PENDENTES: Há migrações para aplicar
# - BANCO_ATUALIZADO: Banco já está atualizado
# - BANCO_NAO_EXISTE: Erro de conexão
```

### 2. `.deployignore`
**Função**: Define arquivos/pastas que NÃO devem ser enviados no deploy

```bash
# Principais exclusões:
static/          # ❌ NUNCA sobrescrever uploads
uploads/         # ❌ NUNCA sobrescrever mídia
*.log           # ❌ Não enviar logs locais
__pycache__/    # ❌ Cache Python
```

### 3. `scripts/backup.sh`
**Função**: Realiza backup de dados críticos antes de deploys

```bash
# Uso:
./scripts/backup.sh production full      # Backup completo
./scripts/backup.sh homolog data-only    # Apenas dados
```

### 4. `docker-compose.yml` (Atualizado)
**Melhorias**:
- Volumes nomeados e persistentes
- Labels para identificação
- Health checks melhorados
- Configurações específicas do Feed API

---

## 🔄 Novo Fluxo de Deploy

### **Antes (Problemático):**
```bash
1. Transferir TODOS os arquivos (incluindo static/)
2. Aplicar migrações sempre
3. Iniciar containers
4. Torcer para não dar problema
```

### **Agora (Seguro):**
```bash
1. 🔍 Verificar estado do banco
2. 💾 Backup automático (produção)
3. 📤 Transferir apenas código (SEM static/)
4. 🛡️ Garantir volumes persistentes
5. 🔄 Aplicar migrações condicionalmente
6. 🚀 Iniciar containers com volumes
7. ✅ Verificar saúde da aplicação
```

---

## 📊 Comparação: Antes vs Depois

| Aspecto | ❌ Antes | ✅ Depois |
|---------|----------|-----------|
| **Banco** | Sempre recriava | Verifica estado primeiro |
| **Static** | Sobrescrevia uploads | PROTEGIDO - nunca sobrescreve |
| **Backup** | Manual/inexistente | Automático para produção |
| **Volumes** | Perdidos no deploy | Persistentes com labels |
| **Segurança** | Risco de perda de dados | Múltiplas camadas de proteção |
| **Rollback** | Difícil/impossível | Backups automáticos |

---

## 🛡️ Proteções Implementadas

### 1. **Proteção de Dados do Usuário**
```bash
# ❌ NUNCA mais será enviado no deploy:
static/uploads/      # Imagens dos feeds
static/media/        # Mídia dos usuários
logs/               # Logs da aplicação
```

### 2. **Verificação de Banco Inteligente**
```bash
# ✅ Deploy detecta automaticamente:
- Primeira instalação → Cria estrutura + dados iniciais
- Migrações pendentes → Aplica apenas o necessário
- Banco atualizado → Pula migrações
```

### 3. **Backup Automático**
```bash
# ✅ Para produção, backup automático de:
- Banco de dados (SQL dump)
- Volumes Docker (tar.gz)
- Configurações (docker-compose, .env)
- Logs dos containers
```

### 4. **Volumes Persistentes**
```yaml
# ✅ Dados preservados entre deploys:
volumes:
  feed-static:     # Arquivos estáticos
  feed-uploads:    # Uploads dos usuários
  feed-media:      # Mídia dos feeds
  redis-data:      # Cache Redis
```

---

## 🚀 Como Usar as Melhorias

### **Deploy Normal (Homologação)**
```bash
# Script detecta automaticamente o que fazer
make deploy-homolog
```

### **Deploy Produção**
```bash
# Backup automático + confirmação obrigatória
make deploy-production
```

### **Backup Manual**
```bash
# Backup completo
./scripts/backup.sh production full

# Apenas dados
./scripts/backup.sh production data-only
```

### **Forçar Backup (Homologação)**
```bash
# Para forçar backup em homolog
FORCE_BACKUP=1 ./scripts/deploy.sh homolog
```

---

## 📋 Checklist de Segurança

### ✅ **Antes do Deploy:**
- [ ] Código commitado e testado
- [ ] Variáveis de ambiente configuradas
- [ ] Backup recente disponível (produção)
- [ ] Equipe notificada sobre deploy

### ✅ **Durante o Deploy:**
- [ ] Script verifica estado do banco ✓
- [ ] Backup automático executado ✓
- [ ] Static/ protegido ✓
- [ ] Volumes preservados ✓
- [ ] Health checks passando ✓

### ✅ **Após o Deploy:**
- [ ] API respondendo
- [ ] Uploads funcionando
- [ ] Redis operacional
- [ ] Logs sem erros
- [ ] Dados preservados

---

## 🔧 Comandos Úteis

### **Verificar Estado do Banco**
```bash
# No servidor:
cd /docker/i9-smart/feed_api
python3 check_database.py
```

### **Verificar Volumes**
```bash
# Listar volumes
docker volume ls | grep feed

# Inspecionar volume
docker volume inspect feed-static
```

### **Verificar Backups**
```bash
# No servidor:
ls -la /backup/i9-feed/
```

### **Logs Detalhados**
```bash
# Logs da API
docker logs i9-feed-api

# Logs do Redis
docker logs i9-feed-redis
```

---

## 🆘 Troubleshooting

### **Problema: "Banco não existe"**
```bash
# Solução: Verificar string de conexão
echo $DATABASE_URL
# Garantir que banco PostgreSQL está rodando
```

### **Problema: "Volume não encontrado"**
```bash
# Solução: Recriar volumes
docker volume create feed-static
docker volume create feed-uploads
```

### **Problema: "Static não carrega"**
```bash
# Verificar se volume está montado
docker inspect i9-feed-api | grep -A 10 Mounts
```

### **Problema: "Migrações falharam"**
```bash
# Verificar estado manualmente
docker exec i9-feed-api alembic current
docker exec i9-feed-api alembic heads
```

---

## 📈 Benefícios das Melhorias

### **Para Desenvolvedores:**
- ✅ Deploys mais seguros e confiáveis
- ✅ Menos chance de perder dados
- ✅ Rollback mais fácil com backups
- ✅ Logs mais claros sobre o que acontece

### **Para Usuários:**
- ✅ Uploads nunca são perdidos
- ✅ Feeds continuam funcionando
- ✅ Zero downtime em uploads
- ✅ Dados sempre preservados

### **Para Operação:**
- ✅ Backups automáticos
- ✅ Monitoramento melhorado
- ✅ Recovery mais rápido
- ✅ Auditoria completa dos deploys

---

## 🔮 Próximos Passos

### **Melhorias Futuras:**
1. **Script de restore automático**
2. **Monitoramento de volumes**
3. **Backup incremental**
4. **Deploy blue-green**
5. **Testes automatizados pré-deploy**

### **Monitoramento:**
1. **Alertas de backup**
2. **Métricas de volume**
3. **Health checks avançados**
4. **Dashboards de deploy**

---

## 📞 Suporte

Para dúvidas ou problemas:

1. **Verificar logs**: `make deploy-logs`
2. **Status containers**: `make deploy-status`
3. **SSH no servidor**: `make deploy-ssh`
4. **Documentação**: Este arquivo + DEPLOY.md

---

**✨ Deploy Seguro = Dados Protegidos = Usuários Felizes**

*Última atualização: 2025-01-30*