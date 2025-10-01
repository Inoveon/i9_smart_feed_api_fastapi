# 📚 Documentação Completa da API i9 Smart Feed

## 🎯 Visão Geral

A **i9 Smart Feed API** é uma API RESTful desenvolvida em FastAPI para gerenciamento de campanhas publicitárias com imagens exibidas em tablets/totems distribuídos em múltiplos postos de combustível. Esta documentação serve como referência completa para desenvolvedores frontend, mobile e integrações.

### Características Principais

- **Targeting Hierárquico**: 4 níveis (Global → Regional → Filial → Estação)
- **Upload Múltiplo**: Suporte a upload de múltiplas imagens simultâneas
- **Agendamento**: Campanhas com data/hora de início e fim
- **Analytics**: Métricas em tempo real e relatórios customizáveis
- **Cache Inteligente**: Redis para otimização de performance
- **API para Tablets**: Endpoint específico para dispositivos

## 🔗 Base URLs e Ambiente

### Desenvolvimento
```yaml
Base URL: http://localhost:8000
API Base: http://localhost:8000/api
Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
```

### Produção
```yaml
Base URL: https://api.i9smart.com.br
API Base: https://api.i9smart.com.br/api
```

## 🔐 Autenticação

### 1. Portal Administrativo - JWT Bearer Token

**Fluxo de Autenticação:**
1. Login → Recebe `access_token` (60 min) e `refresh_token` (7 dias)
2. Requisições → Header: `Authorization: Bearer {access_token}`
3. Renovação → Endpoint `/auth/refresh` com `refresh_token`

#### Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

**Resposta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Renovar Token
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 2. Tablets/Totems - API Key

**Header obrigatório:**
```http
X-API-Key: i9smart_campaigns_readonly_2025
```

## 📋 Endpoints Completos

### 🔐 Autenticação (`/api/auth`)

| Método | Endpoint | Descrição | Auth | Roles |
|--------|----------|-----------|------|-------|
| POST | `/login` | Login com username/email e senha | - | - |
| POST | `/refresh` | Renovar access token | - | - |
| GET | `/me` | Dados do usuário logado | JWT | todos |
| PUT | `/me` | Atualizar perfil | JWT | todos |
| PUT | `/me/password` | Alterar senha | JWT | todos |
| DELETE | `/me` | Desativar conta | JWT | todos |

#### Exemplo - Obter Perfil do Usuário
```http
GET /api/auth/me
Authorization: Bearer {token}
```

**Resposta:**
```json
{
  "id": "uuid",
  "email": "admin@i9smart.com.br",
  "username": "admin",
  "full_name": "Administrador",
  "role": "admin",
  "is_active": true,
  "is_verified": true,
  "preferences": {
    "theme": "light",
    "palette": "blue"
  },
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-20T10:30:00Z",
  "token_info": {
    "expires_in_seconds": 3540,
    "expires_at": "2025-01-20T11:30:00Z"
  }
}
```

### 📢 Campanhas (`/api/campaigns`)

| Método | Endpoint | Descrição | Auth | Roles |
|--------|----------|-----------|------|-------|
| GET | `/` | Listar campanhas | JWT | todos |
| POST | `/` | Criar campanha | JWT | admin, editor |
| GET | `/active` | Campanhas ativas (todas) | JWT | todos |
| GET | `/active/{station_code}` | Campanhas ativas por estação | JWT | todos |
| GET | `/{id}` | Obter campanha específica | JWT | todos |
| PUT | `/{id}` | Atualizar campanha | JWT | admin, editor |
| DELETE | `/{id}` | Deletar campanha (soft delete) | JWT | admin |
| GET | `/{id}/metrics` | Métricas da campanha | JWT | todos |

#### Exemplo - Criar Campanha
```http
POST /api/campaigns/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Black Friday 2025",
  "description": "Ofertas especiais de Black Friday",
  "status": "scheduled",
  "start_date": "2025-11-25T00:00:00Z",
  "end_date": "2025-11-30T23:59:59Z",
  "default_display_time": 5000,
  "regions": ["Sudeste", "Sul"],
  "branches": [],
  "stations": [],
  "priority": 90
}
```

**Resposta:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Black Friday 2025",
  "description": "Ofertas especiais de Black Friday",
  "status": "scheduled",
  "start_date": "2025-11-25T00:00:00Z",
  "end_date": "2025-11-30T23:59:59Z",
  "default_display_time": 5000,
  "regions": ["Sudeste", "Sul"],
  "branches": [],
  "stations": [],
  "priority": 90,
  "is_deleted": false,
  "created_by": "user-uuid",
  "created_at": "2025-01-20T10:30:00Z",
  "updated_at": "2025-01-20T10:30:00Z"
}
```

#### Exemplo - Campanhas Ativas por Estação
```http
GET /api/campaigns/active/001
Authorization: Bearer {token}
```

**Resposta:**
```json
{
  "station_code": "001",
  "branch_code": "01",
  "region": "Sudeste",
  "campaigns": [
    {
      "id": "uuid",
      "name": "Promoção Verão",
      "description": "Descontos especiais",
      "default_display_time": 5000,
      "priority": 90,
      "targeting_level": "branch"
    }
  ],
  "total": 1,
  "timestamp": "2025-01-20T10:30:00Z"
}
```

### 🖼️ Imagens (`/api/campaigns/{id}/images` e `/api/images`)

| Método | Endpoint | Descrição | Auth | Roles |
|--------|----------|-----------|------|-------|
| GET | `/campaigns/{id}/images` | Listar imagens da campanha | JWT | todos |
| POST | `/campaigns/{id}/images` | Upload múltiplo de imagens | JWT | admin, editor |
| PUT | `/campaigns/{id}/images/order` | Reordenar imagens | JWT | admin, editor |
| DELETE | `/campaigns/{id}/images/{image_id}` | Deletar imagem | JWT | admin, editor |
| PUT | `/images/{id}` | Atualizar dados da imagem | JWT | admin, editor |

#### Exemplo - Upload Múltiplo de Imagens
```http
POST /api/campaigns/{campaign_id}/images
Authorization: Bearer {token}
Content-Type: multipart/form-data

files: [arquivo1.jpg, arquivo2.png, arquivo3.webp]
```

**Resposta:**
```json
{
  "campaign_id": "uuid",
  "campaign_name": "Black Friday 2025",
  "default_display_time": 5000,
  "total": 3,
  "uploaded_count": 3,
  "images": [
    {
      "id": "image-uuid-1",
      "filename": "campaign_uuid_1.jpg",
      "original_filename": "arquivo1.jpg",
      "url": "/static/uploads/campaigns/uuid/campaign_uuid_1.jpg",
      "order": 1,
      "display_time": 5000,
      "title": null,
      "description": null,
      "active": true,
      "size_bytes": 245789,
      "mime_type": "image/jpeg",
      "width": 1920,
      "height": 1080,
      "created_at": "2025-01-20T10:30:00Z"
    }
  ]
}
```

#### Exemplo - Reordenar Imagens
```http
PUT /api/campaigns/{campaign_id}/images/order
Authorization: Bearer {token}
Content-Type: application/json

["image-uuid-3", "image-uuid-1", "image-uuid-2"]
```

#### Exemplo - Atualizar Dados da Imagem
```http
PUT /api/images/{image_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "Banner Principal",
  "description": "Imagem de destaque da campanha",
  "display_time": 7000,
  "active": true
}
```

### 👥 Usuários (`/api/users`)

| Método | Endpoint | Descrição | Auth | Roles |
|--------|----------|-----------|------|-------|
| GET | `/` | Listar usuários (paginado) | JWT | admin |
| POST | `/` | Criar usuário | JWT | admin |
| GET | `/statistics` | Estatísticas de usuários | JWT | admin |
| GET | `/{user_id}` | Obter usuário específico | JWT | admin |
| PUT | `/{user_id}` | Atualizar usuário | JWT | admin |
| DELETE | `/{user_id}` | Desativar usuário | JWT | admin |
| PUT | `/{user_id}/password` | Resetar senha | JWT | admin |

### 🏢 Filiais (`/api/branches`)

| Método | Endpoint | Descrição | Auth | Roles |
|--------|----------|-----------|------|-------|
| GET | `/` | Listar filiais (paginado) | JWT | todos |
| GET | `/regions` | Listar regiões e estados | JWT | todos |
| GET | `/active` | Filiais ativas | JWT | todos |
| GET | `/by-code/{code}` | Buscar por código | JWT | todos |
| GET | `/{id}` | Detalhes da filial | JWT | todos |
| POST | `/` | Criar filial | JWT | admin |
| PUT | `/{id}` | Atualizar filial | JWT | admin |
| DELETE | `/{id}` | Desativar filial | JWT | admin |
| GET | `/{id}/statistics` | Estatísticas da filial | JWT | todos |

#### Exemplo - Listar Filiais
```http
GET /api/branches?page=1&limit=10&search=São Paulo&region=Sudeste
Authorization: Bearer {token}
```

**Resposta:**
```json
{
  "items": [
    {
      "id": "uuid",
      "code": "01001",
      "name": "Posto São Paulo Centro",
      "city": "São Paulo",
      "state": "SP",
      "region": "Sudeste",
      "is_active": true,
      "stations_count": 5,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  ],
  "page": 1,
  "page_size": 10,
  "total": 1,
  "total_pages": 1,
  "has_next": false,
  "has_prev": false
}
```

### 📍 Estações (`/api/stations`)

| Método | Endpoint | Descrição | Auth | Roles |
|--------|----------|-----------|------|-------|
| GET | `/` | Listar estações (paginado) | JWT | todos |
| GET | `/active` | Estações ativas | JWT | todos |
| GET | `/available` | Estrutura completa filiais/estações | JWT | todos |
| GET | `/by-branch-and-code/{branch_code}/{station_code}` | Buscar por códigos | JWT | todos |
| GET | `/{id}` | Detalhes da estação | JWT | todos |
| POST | `/` | Criar estação | JWT | admin |
| PUT | `/{id}` | Atualizar estação | JWT | admin |
| DELETE | `/{id}` | Desativar estação | JWT | admin |
| GET | `/branches/{branch_id}/stations` | Estações de uma filial | JWT | todos |

#### Exemplo - Estrutura Disponível
```http
GET /api/stations/available
Authorization: Bearer {token}
```

**Resposta:**
```json
{
  "regions": {
    "Sudeste": [
      {
        "code": "01001",
        "name": "Posto São Paulo Centro",
        "state": "SP"
      }
    ]
  },
  "branches": {
    "01001": {
      "name": "Posto São Paulo Centro",
      "state": "SP",
      "region": "Sudeste",
      "stations": [
        {
          "code": "001",
          "name": "Caixa 1"
        },
        {
          "code": "002",
          "name": "Caixa 2"
        }
      ]
    }
  }
}
```

### 📊 Analytics (`/api/analytics`)

| Método | Endpoint | Descrição | Auth | Roles |
|--------|----------|-----------|------|-------|
| GET | `/` | Dashboard geral com KPIs | JWT | todos |
| GET | `/comparison` | Comparação entre períodos | JWT | todos |
| GET | `/regions` | Analytics por região | JWT | todos |

#### Exemplo - Dashboard Analytics
```http
GET /api/analytics?period=30
Authorization: Bearer {token}
```

**Resposta:**
```json
{
  "timestamp": "2025-01-20T10:30:00Z",
  "period": {
    "days": 30,
    "start": "2024-12-21T10:30:00Z",
    "end": "2025-01-20T10:30:00Z"
  },
  "kpis": {
    "total_campaigns": 45,
    "active_campaigns": 12,
    "total_images": 234,
    "activation_rate": 26.67,
    "growth_rate": 15.2
  },
  "comparisons": {
    "current_period": {
      "campaigns": 18,
      "period_days": 30
    },
    "previous_period": {
      "campaigns": 15,
      "period_days": 30
    },
    "change_percentage": 20.0
  },
  "trends": {
    "daily": [
      {
        "date": "2025-01-20",
        "total": 3,
        "active": 2
      }
    ]
  },
  "top_creators": [
    {
      "username": "admin",
      "email": "admin@i9smart.com.br",
      "campaigns": 25
    }
  ]
}
```

### 📄 Relatórios (`/api/reports`)

| Método | Endpoint | Descrição | Auth | Roles |
|--------|----------|-----------|------|-------|
| GET | `/` | Gerar relatórios customizados | JWT | todos |
| GET | `/export` | Exportar dados (CSV/JSON) | JWT | admin, editor |
| GET | `/templates` | Templates pré-configurados | JWT | todos |

#### Exemplo - Exportar Relatório
```http
GET /api/reports/export?format=csv&data_type=campaigns&start_date=2025-01-01&end_date=2025-01-31
Authorization: Bearer {token}
```

### 🏥 Health Check (`/health` e `/api/health`)

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/health/` | Health check básico | - |
| GET | `/health/live` | Liveness probe | - |
| GET | `/health/ready` | Readiness probe | - |
| GET | `/health/detailed` | Check detalhado de componentes | - |

#### Exemplo - Health Check Detalhado
```http
GET /health/detailed
```

**Resposta:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-20T10:30:00Z",
  "service": "i9 Smart Campaigns API",
  "version": "1.0.0",
  "environment": "development",
  "components": {
    "database": {
      "status": "healthy",
      "latency_ms": 15.2,
      "stats": {
        "campaigns": 45,
        "users": 8
      }
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 2.1,
      "stats": {
        "used_memory_human": "1.2M",
        "connected_clients": 3
      }
    },
    "system": {
      "status": "healthy",
      "cpu": {
        "usage_percent": 15.3,
        "cores": 8
      },
      "memory": {
        "usage_percent": 45.2,
        "available_gb": 4.2,
        "total_gb": 8.0
      }
    }
  }
}
```

### 🔧 Admin (`/api/admin`)

| Método | Endpoint | Descrição | Auth | Roles |
|--------|----------|-----------|------|-------|
| POST | `/sync/branches` | Sincronizar filiais do Protheus | JWT | admin |
| GET | `/sync/status/{sync_id}` | Status de sincronização | JWT | admin |
| GET | `/sync/history` | Histórico de sincronizações | JWT | admin |
| GET | `/stats/overview` | Estatísticas do sistema | JWT | admin |
| GET | `/scheduler/jobs` | Jobs agendados | JWT | admin |
| POST | `/scheduler/trigger/{job_id}` | Executar job manualmente | JWT | admin |

### 📱 Tablets (`/api/tablets`)

**Requer API Key:** `X-API-Key: i9smart_campaigns_readonly_2025`

| Método | Endpoint | Descrição | Auth |
|--------|----------|-----------|------|
| GET | `/active` | Todas campanhas ativas | API Key |
| GET | `/active/{station_code}` | Campanhas ativas por estação | API Key |
| GET | `/images/{image_id}` | Download de imagem | API Key |
| HEAD | `/images/{image_id}` | Check de cache de imagem | API Key |

#### Exemplo - Campanhas para Tablet
```http
GET /api/tablets/active/001
X-API-Key: i9smart_campaigns_readonly_2025
```

**Resposta:**
```json
{
  "station_code": "001",
  "branch_code": "01001",
  "region": "Sudeste",
  "campaigns": [
    {
      "id": "uuid",
      "name": "Promoção Verão",
      "description": "Descontos especiais",
      "default_display_time": 5000,
      "priority": 90,
      "targeting_level": "branch",
      "start_date": "2025-01-01T00:00:00Z",
      "end_date": "2025-01-31T23:59:59Z",
      "images": [
        {
          "id": "image-uuid",
          "campaign_id": "uuid",
          "order_index": 1,
          "display_time": 5000,
          "width": 1920,
          "height": 1080,
          "mime_type": "image/jpeg",
          "size_bytes": 245789,
          "checksum": "d41d8cd98f00b204e9800998ecf8427e",
          "download_url": "/api/tablets/images/image-uuid"
        }
      ]
    }
  ],
  "total": 1,
  "timestamp": "2025-01-20T10:30:00Z",
  "cache_ttl": 120
}
```

## 📊 Modelos de Dados Detalhados

### Campaign
```typescript
interface Campaign {
  id: string;                          // UUID
  name: string;                        // Nome da campanha (3-255 chars)
  description?: string;                // Descrição opcional
  status: 'active' | 'scheduled' | 'paused' | 'expired';
  start_date: DateTime;                // ISO 8601
  end_date: DateTime;                  // ISO 8601
  default_display_time: number;        // Milissegundos (1000-60000)
  
  // Targeting hierárquico
  regions: string[];                   // ["Norte", "Sudeste"]
  branches: string[];                  // ["01001", "02001"]
  stations: string[];                  // ["001", "002"]
  
  priority: number;                    // 0-100 (default: 0)
  is_deleted: boolean;                 // Soft delete
  created_by?: string;                 // UUID do criador
  created_at: DateTime;
  updated_at: DateTime;
}
```

### CampaignImage
```typescript
interface CampaignImage {
  id: string;                          // UUID
  campaign_id: string;                 // UUID da campanha
  filename: string;                    // Nome no storage
  original_filename?: string;          // Nome original
  url: string;                         // URL completa
  order: number;                       // Posição (1, 2, 3...)
  display_time?: number;               // Override em ms
  title?: string;                      // Título opcional
  description?: string;                // Descrição opcional
  active: boolean;                     // Ativa/inativa
  size_bytes?: number;                 // Tamanho do arquivo
  mime_type?: string;                  // image/jpeg, image/png, image/webp
  width?: number;                      // Largura em pixels
  height?: number;                     // Altura em pixels
  created_at: DateTime;
  updated_at: DateTime;
}
```

### User
```typescript
interface User {
  id: string;                          // UUID
  email: string;                       // Email único (lowercase)
  username: string;                    // Username único (3-50 chars)
  full_name?: string;                  // Nome completo
  role: 'admin' | 'editor' | 'viewer'; // Role do usuário
  is_active: boolean;                  // Conta ativa
  is_verified: boolean;                // Email verificado
  preferences: {
    theme: 'light' | 'dark';
    palette: 'blue' | 'emerald' | 'violet' | 'rose' | 'amber';
  };
  last_login?: DateTime;               // Último login
  created_at: DateTime;
  updated_at: DateTime;
}
```

### Branch
```typescript
interface Branch {
  id: string;                          // UUID
  code: string;                        // Código único da filial
  name: string;                        // Nome da filial
  city?: string;                       // Cidade
  state: string;                       // UF (2 chars)
  region: string;                      // Região calculada
  is_active: boolean;                  // Ativa/inativa
  stations_count: number;              // Quantidade de estações
  created_at: DateTime;
  updated_at: DateTime;
}
```

### Station
```typescript
interface Station {
  id: string;                          // UUID
  code: string;                        // Código na filial
  name: string;                        // Nome da estação
  branch_id: string;                   // UUID da filial
  branch?: Branch;                     // Dados da filial
  address?: string;                    // Endereço opcional
  is_active: boolean;                  // Ativa/inativa
  created_at: DateTime;
  updated_at: DateTime;
}
```

## 🎯 Sistema de Targeting Hierárquico

### Níveis de Targeting (4 níveis)

1. **Global** - Todas as estações (arrays vazios)
```json
{
  "regions": [],
  "branches": [],
  "stations": []
}
```

2. **Regional** - Todas estações da região
```json
{
  "regions": ["Sudeste", "Sul"],
  "branches": [],
  "stations": []
}
```

3. **Por Filial** - Todas estações das filiais
```json
{
  "regions": [],
  "branches": ["01001", "02002"],
  "stations": []
}
```

4. **Por Estação** - Estações específicas
```json
{
  "regions": [],
  "branches": ["01001"],
  "stations": ["001", "002"]
}
```

### Regiões Brasileiras Disponíveis
- **Norte**: AC, AM, AP, PA, RO, RR, TO
- **Nordeste**: AL, BA, CE, MA, PB, PE, PI, RN, SE
- **Centro-Oeste**: DF, GO, MS, MT
- **Sudeste**: ES, MG, RJ, SP
- **Sul**: PR, RS, SC

## ⚠️ Regras de Negócio e Validações

### Upload de Imagens

**Formatos Aceitos:**
- JPEG/JPG
- PNG
- WebP

**Limites:**
- Tamanho máximo: 10MB por arquivo
- Upload simultâneo: até 10 arquivos
- Total por campanha: ilimitado

**Processamento Automático:**
- Redimensionamento se > 1920x1080
- Otimização de qualidade
- Geração de thumbnails
- Conversão para WebP (quando solicitado)

**Display Time:**
- Mínimo: 1000ms (1 segundo)
- Máximo: 60000ms (60 segundos)
- Padrão: 5000ms (5 segundos)

### Validações de Campanha

```typescript
// Validações aplicadas automaticamente
interface CampaignValidation {
  name: string;                        // Obrigatório, 3-255 chars
  start_date: DateTime;                // Obrigatório
  end_date: DateTime;                  // Obrigatório, > start_date
  regions: string[];                   // Deve existir em REGIONS
  stations: string[];                  // Requer branches se informado
  priority: number;                    // 0-100
  default_display_time: number;       // 1000-60000ms
}
```

### Hierarquia de Permissões

| Ação | Admin | Editor | Viewer |
|------|-------|--------|--------|
| Criar campanhas | ✅ | ✅ | ❌ |
| Editar campanhas | ✅ | ✅ | ❌ |
| Deletar campanhas | ✅ | ❌ | ❌ |
| Upload imagens | ✅ | ✅ | ❌ |
| Ver campanhas | ✅ | ✅ | ✅ |
| Analytics | ✅ | ✅ | ✅ |
| Gerenciar usuários | ✅ | ❌ | ❌ |
| Admin endpoints | ✅ | ❌ | ❌ |

## 🔄 Paginação Padrão

**Parâmetros de Query:**
```typescript
interface PaginationParams {
  page: number;                        // Página atual (default: 1)
  limit: number;                       // Itens por página (1-100, default: 10)
  search?: string;                     // Busca textual
  sort?: string;                       // Campo de ordenação
  order?: 'asc' | 'desc';             // Direção (default: asc)
}
```

**Formato de Resposta:**
```typescript
interface PaginatedResponse<T> {
  items: T[];                          // Itens da página atual
  page: number;                        // Página atual
  page_size: number;                   // Itens por página
  total: number;                       // Total de itens
  total_pages: number;                 // Total de páginas
  has_next: boolean;                   // Tem próxima página
  has_prev: boolean;                   // Tem página anterior
}
```

## 🛡️ Códigos de Status HTTP

| Código | Situação | Descrição |
|--------|----------|-----------|
| 200 | OK | Sucesso |
| 201 | Created | Recurso criado |
| 204 | No Content | Sucesso sem conteúdo |
| 400 | Bad Request | Dados inválidos |
| 401 | Unauthorized | Token inválido/expirado |
| 403 | Forbidden | Sem permissão |
| 404 | Not Found | Recurso não encontrado |
| 409 | Conflict | Conflito (ex: duplicado) |
| 422 | Unprocessable Entity | Erro de validação |
| 429 | Too Many Requests | Rate limit excedido |
| 500 | Internal Server Error | Erro do servidor |

## 🚀 Exemplos Práticos Completos

### Fluxo Completo - Criar Campanha com Imagens

```javascript
class CampaignManager {
  constructor(apiUrl, token) {
    this.apiUrl = apiUrl;
    this.token = token;
  }

  async createCompleteCampaign(campaignData, imageFiles) {
    try {
      // 1. Criar campanha
      const campaign = await this.createCampaign(campaignData);
      console.log('Campanha criada:', campaign.id);

      // 2. Upload das imagens
      if (imageFiles.length > 0) {
        const images = await this.uploadImages(campaign.id, imageFiles);
        console.log(`${images.uploaded_count} imagens enviadas`);
      }

      // 3. Ativar campanha
      const activatedCampaign = await this.updateCampaign(campaign.id, {
        status: 'active'
      });

      return activatedCampaign;
    } catch (error) {
      console.error('Erro ao criar campanha:', error);
      throw error;
    }
  }

  async createCampaign(data) {
    const response = await fetch(`${this.apiUrl}/api/campaigns/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Erro ao criar campanha');
    }

    return response.json();
  }

  async uploadImages(campaignId, files, metadata = []) {
    const formData = new FormData();
    
    files.forEach((file, index) => {
      formData.append('files', file);
    });

    if (metadata.length > 0) {
      formData.append('metadata', JSON.stringify(metadata));
    }

    const response = await fetch(
      `${this.apiUrl}/api/campaigns/${campaignId}/images`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token}`
        },
        body: formData
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Erro ao enviar imagens');
    }

    return response.json();
  }

  async updateCampaign(campaignId, data) {
    const response = await fetch(
      `${this.apiUrl}/api/campaigns/${campaignId}`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Erro ao atualizar campanha');
    }

    return response.json();
  }
}

// Exemplo de uso
const manager = new CampaignManager('http://localhost:8000', token);

const campaignData = {
  name: 'Natal 2025',
  description: 'Campanha especial de Natal',
  start_date: '2025-12-01T00:00:00Z',
  end_date: '2025-12-31T23:59:59Z',
  default_display_time: 6000,
  regions: ['Sudeste'],
  priority: 95
};

const imageFiles = [file1, file2, file3];

manager.createCompleteCampaign(campaignData, imageFiles)
  .then(campaign => {
    console.log('Campanha completa criada:', campaign);
  })
  .catch(error => {
    console.error('Erro:', error.message);
  });
```

### Gerenciamento de Estado no Frontend

```javascript
// Hook React para gerenciar campanhas
import { useState, useEffect } from 'react';

function useCampaigns() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchCampaigns = async (filters = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams(filters);
      const response = await fetch(
        `/api/campaigns?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${getToken()}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('Erro ao carregar campanhas');
      }

      const data = await response.json();
      setCampaigns(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const createCampaign = async (campaignData) => {
    setLoading(true);
    try {
      const response = await fetch('/api/campaigns/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(campaignData)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail);
      }

      const newCampaign = await response.json();
      setCampaigns(prev => [newCampaign, ...prev]);
      return newCampaign;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();
  }, []);

  return {
    campaigns,
    loading,
    error,
    fetchCampaigns,
    createCampaign
  };
}
```

### Componente de Upload de Imagens

```javascript
import { useDropzone } from 'react-dropzone';
import { useState } from 'react';

function ImageUploader({ campaignId, onUploadComplete }) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.webp']
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    maxFiles: 10,
    onDrop: handleUpload
  });

  async function handleUpload(acceptedFiles) {
    if (acceptedFiles.length === 0) return;

    setUploading(true);
    setProgress(0);

    try {
      const formData = new FormData();
      acceptedFiles.forEach(file => {
        formData.append('files', file);
      });

      const xhr = new XMLHttpRequest();
      
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percentComplete = (e.loaded / e.total) * 100;
          setProgress(percentComplete);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          const result = JSON.parse(xhr.responseText);
          onUploadComplete(result);
          setProgress(100);
        } else {
          throw new Error('Erro no upload');
        }
      });

      xhr.open('POST', `/api/campaigns/${campaignId}/images`);
      xhr.setRequestHeader('Authorization', `Bearer ${getToken()}`);
      xhr.send(formData);

    } catch (error) {
      console.error('Erro no upload:', error);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="upload-zone">
      <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
        <input {...getInputProps()} />
        
        {uploading ? (
          <div className="upload-progress">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${progress}%` }}
              />
            </div>
            <p>Enviando... {Math.round(progress)}%</p>
          </div>
        ) : (
          <div className="upload-message">
            {isDragActive ? (
              <p>Solte as imagens aqui...</p>
            ) : (
              <div>
                <p>Arraste imagens aqui ou clique para selecionar</p>
                <small>Máximo 10 arquivos, 10MB cada (JPEG, PNG, WebP)</small>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
```

## 🧪 Testando a API

### cURL Examples

```bash
# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Criar campanha
curl -X POST "http://localhost:8000/api/campaigns/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Teste API",
    "start_date": "2025-01-25T00:00:00Z",
    "end_date": "2025-01-31T23:59:59Z",
    "regions": ["Sudeste"]
  }'

# Upload de imagens
curl -X POST "http://localhost:8000/api/campaigns/$CAMPAIGN_ID/images" \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@image1.jpg" \
  -F "files=@image2.png"

# Listar campanhas ativas para tablet
curl -X GET "http://localhost:8000/api/tablets/active/001" \
  -H "X-API-Key: i9smart_campaigns_readonly_2025"

# Exportar relatório
curl -X GET "http://localhost:8000/api/reports/export?format=csv&data_type=campaigns" \
  -H "Authorization: Bearer $TOKEN" \
  -o campaigns.csv
```

### Postman Collection

Importe via OpenAPI Schema:
```
http://localhost:8000/openapi.json
```

## 🔧 Rate Limiting e Cache

### Rate Limits
- **Portal (JWT)**: 1000 req/min por usuário
- **Tablets (API Key)**: 500 req/min por chave
- **Upload**: 10 uploads/min por usuário

### Cache Strategy
- **Campanhas ativas**: 2 minutos (Redis)
- **Filiais/Estações**: 10 minutos (Redis)
- **Analytics**: 5 minutos (Redis)
- **Imagens**: Cache HTTP + ETag

## 📞 Suporte e Informações

### Informações Técnicas
- **Versão API**: 1.0.0
- **Framework**: FastAPI 0.109+
- **Python**: 3.11+
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Storage**: MinIO (S3-compatible)

### Documentação Adicional
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI Schema**: `/openapi.json`
- **Health Check**: `/health/detailed`

### Versionamento
A API segue versionamento semântico. Mudanças que quebram compatibilidade serão comunicadas com antecedência.

---

**Última atualização**: 20/01/2025  
**Próximas funcionalidades**: WebSockets para notificações real-time, Analytics avançado com IA, Integração com APIs externas