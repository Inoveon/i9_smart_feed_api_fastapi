# A01 - Agente Atualizador de Documentação API

## 📋 Objetivo
Atualizar completamente a documentação da API em docs/API-DOCUMENTATION.md com todos os endpoints, modelos, códigos de erro e exemplos de requisição/resposta.

## 🎯 Tarefas
1. Analisar todos os arquivos de rotas da API
2. Identificar todos os endpoints disponíveis
3. Documentar modelos de requisição e resposta
4. Listar todos os códigos de erro possíveis
5. Adicionar exemplos práticos de cada endpoint
6. Organizar por seções lógicas (Auth, Campaigns, Branches, Stations, Images)
7. Incluir informações de paginação, filtros e ordenação
8. Documentar headers necessários e autenticação
9. Adicionar tabela de status codes
10. Criar índice navegável

## 🔧 Comandos
```bash
# Analisar estrutura de rotas
find app/routes -name "*.py" -type f

# Verificar modelos Pydantic
find app/schemas -name "*.py" -type f

# Verificar endpoints no main.py
grep -r "include_router\|@app\." app/main.py

# Verificar decorators de rotas
grep -r "@router\." app/routes/

# Verificar status codes usados
grep -r "status_code\|HTTPException\|status\." app/

# Verificar modelos de resposta
grep -r "response_model\|Response\[" app/routes/
```

## ✅ Checklist de Validação
- [ ] Todos os endpoints documentados
- [ ] Todos os métodos HTTP corretos
- [ ] Parâmetros de query string documentados
- [ ] Headers obrigatórios especificados
- [ ] Modelos de requisição com tipos de dados
- [ ] Modelos de resposta com exemplos
- [ ] Códigos de erro com descrições
- [ ] Exemplos cURL para cada endpoint
- [ ] Informações de autenticação claras
- [ ] Versionamento da API documentado

## 📊 Resultado Esperado
Arquivo docs/API-DOCUMENTATION.md completo com:
- Documentação OpenAPI 3.0 compatible
- Todos os endpoints da API
- Exemplos de requisição e resposta
- Códigos de status HTTP
- Modelos de dados detalhados
- Guia de autenticação
- Informações de rate limiting
- Changelog da API