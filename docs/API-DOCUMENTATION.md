# 📚 Documentação Completa da API i9 Smart Campaigns

## 🎯 Visão Geral

A **i9 Smart Campaigns API** é uma API RESTful desenvolvida em FastAPI para gerenciamento de campanhas publicitárias em tablets/totems distribuídos em múltiplos postos. Esta documentação serve como referência completa para equipes que irão desenvolver o portal administrativo e integrar com a API.

## 🔐 Informações de Acesso

### Ambiente de Desenvolvimento

```yaml
Base URL: http://localhost:8000
API Documentation: http://localhost:8000/docs (Swagger UI)
ReDoc: http://localhost:8000/redoc
```

### Credenciais Padrão

#### Portal Administrativo (JWT)
```yaml
Username: admin
Password: admin123
Email: admin@i9smart.com.br
Role: admin
```

#### Tablets/Totems (API Key)
```yaml
API Key: i9smart_campaigns_readonly_2025
Header: X-API-Key
```

### Banco de Dados

```yaml
Host: 10.0.10.5
Port: 5432
Database: i9_campaigns
Username: campaigns_user
Password: Camp@2025#Secure
```

## 🔑 Autenticação

### 1. Portal Administrativo - JWT

O portal usa autenticação JWT com Bearer Token. O fluxo é:

1. **Login** → Recebe `access_token` e `refresh_token`
2. **Requisições** → Envia `Bearer {access_token}` no header
3. **Renovação** → Usa `refresh_token` para obter novo `access_token`

#### Exemplo de Login

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**Resposta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "username": "admin",
    "email": "admin@i9smart.com.br",
    "full_name": "Administrador",
    "role": "admin",
    "preferences": {
      "theme": "light",
      "palette": "blue"
    }
  }
}
```

### 2. Tablets - API Key

Tablets usam API Key no header para acesso somente leitura:

```bash
curl -X GET "http://localhost:8000/api/tablets/active/001" \
  -H "X-API-Key: i9smart_campaigns_readonly_2025"
```

## 📋 Endpoints da API

### 🔐 Autenticação (`/api/auth`)

| Método | Endpoint | Descrição | Autenticação |
|--------|----------|-----------|--------------|
| POST | `/api/auth/login` | Login e obtenção de tokens | Não |
| POST | `/api/auth/refresh` | Renovar access token | Não |
| GET | `/api/auth/me` | Dados do usuário logado | JWT |
| PUT | `/api/auth/me` | Atualizar perfil e preferências | JWT |
| PUT | `/api/auth/password` | Alterar senha | JWT |

### 📢 Campanhas (`/api/campaigns`)

| Método | Endpoint | Descrição | Autenticação | Roles |
|--------|----------|-----------|--------------|-------|
| GET | `/api/campaigns/` | Listar todas campanhas | JWT | todos |
| POST | `/api/campaigns/` | Criar nova campanha | JWT | admin, editor |
| GET | `/api/campaigns/{id}` | Obter campanha específica | JWT | todos |
| PUT | `/api/campaigns/{id}` | Atualizar campanha | JWT | admin, editor |
| DELETE | `/api/campaigns/{id}` | Remover campanha (soft delete) | JWT | admin |
| GET | `/api/campaigns/active/{station_id}` | Campanhas ativas por posto | JWT | todos |
| GET | `/api/campaigns/{id}/metrics` | Métricas da campanha | JWT | todos |

### 🖼️ Imagens (`/api/campaigns/{id}/images`)

| Método | Endpoint | Descrição | Autenticação | Roles |
|--------|----------|-----------|--------------|-------|
| POST | `/api/campaigns/{id}/images` | Upload de imagens (múltiplas) | JWT | admin, editor |
| GET | `/api/campaigns/{id}/images` | Listar imagens da campanha | JWT | todos |
| PUT | `/api/campaigns/{id}/images/order` | Reordenar imagens | JWT | admin, editor |
| DELETE | `/api/campaigns/{id}/images/{image_id}` | Remover imagem específica | JWT | admin, editor |
| PUT | `/api/images/{id}` | Atualizar dados da imagem | JWT | admin, editor |
| GET | `/api/images/{id}` | Obter dados da imagem | JWT | todos |

### 🏢 Filiais (`/api/branches`)

| Método | Endpoint | Descrição | Autenticação | Roles |
|--------|----------|-----------|--------------|-------|
| GET | `/api/branches` | Listar filiais (paginado) | JWT | todos |
| GET | `/api/branches/{code}` | Obter filial específica | JWT | todos |
| GET | `/api/branches/active` | Filiais ativas | JWT | todos |

### 📍 Estações (`/api/stations`)

| Método | Endpoint | Descrição | Autenticação | Roles |
|--------|----------|-----------|--------------|-------|
| GET | `/api/stations` | Listar estações (paginado) | JWT | todos |
| GET | `/api/stations/{branch}/{code}` | Estação específica | JWT | todos |
| GET | `/api/stations/available` | Estações disponíveis | JWT | todos |

### 📊 Analytics (`/api/analytics`)

| Método | Endpoint | Descrição | Autenticação | Roles |
|--------|----------|-----------|--------------|-------|
| GET | `/api/analytics` | Dashboard geral com KPIs | JWT | todos |
| GET | `/api/analytics/comparison` | Comparação entre períodos | JWT | todos |
| GET | `/api/analytics/regions` | Analytics por região | JWT | todos |

### 📈 Métricas (`/api/metrics`)

| Método | Endpoint | Descrição | Autenticação | Roles |
|--------|----------|-----------|--------------|-------|
| GET | `/api/metrics/dashboard` | Métricas do dashboard | JWT | todos |
| GET | `/api/metrics/activity` | Atividade do sistema | JWT | todos |
| GET | `/api/metrics/stations` | Métricas por estação | JWT | todos |
| GET | `/api/metrics/system` | Métricas do sistema | JWT | admin |

### 📄 Relatórios (`/api/reports`)

| Método | Endpoint | Descrição | Autenticação | Roles |
|--------|----------|-----------|--------------|-------|
| GET | `/api/reports` | Gerar relatórios customizados | JWT | todos |
| GET | `/api/reports/export` | Exportar dados (CSV/JSON) | JWT | admin, editor |
| GET | `/api/reports/templates` | Templates de relatórios | JWT | todos |

### 📱 Tablets (`/api/tablets`)

| Método | Endpoint | Descrição | Autenticação |
|--------|----------|-----------|--------------|
| GET | `/api/tablets/active/{station_id}` | Campanhas ativas (read-only) | API Key |

## 📊 Modelos de Dados

### Campaign

```typescript
interface Campaign {
  id: string;                    // UUID
  name: string;                  // Nome da campanha
  description?: string;          // Descrição opcional
  status: 'active' | 'scheduled' | 'paused' | 'expired';
  start_date: DateTime;          // Data/hora início
  end_date: DateTime;            // Data/hora fim
  default_display_time: number;  // Tempo em ms (padrão: 5000)
  
  // Targeting hierárquico (4 níveis)
  stations?: string[];           // Nível 4: Estações específicas
  branches?: string[];           // Nível 3: Filiais
  regions?: string[];            // Nível 2: Regiões (Norte, Sul, etc)
  // Nível 1: Global (quando todos vazios)
  
  priority: number;              // 0-100 (maior = mais importante)
  is_deleted: boolean;           // Soft delete
  created_at: DateTime;
  updated_at: DateTime;
  created_by?: string;           // UUID do usuário
}
```

### CampaignImage

```typescript
interface CampaignImage {
  id: string;                    // UUID
  campaign_id: string;           // UUID da campanha
  filename: string;              // Nome do arquivo no storage
  original_filename?: string;    // Nome original do upload
  url: string;                   // URL completa da imagem
  order_index: number;           // Ordem de exibição (0, 1, 2...)
  display_time?: number;         // Override do tempo (ms)
  title?: string;                // Título opcional
  description?: string;          // Descrição opcional
  active: boolean;               // Se está ativa
  size_bytes?: number;           // Tamanho em bytes
  mime_type?: string;            // image/jpeg, image/png
  width?: number;                // Largura em pixels
  height?: number;               // Altura em pixels
  created_at: DateTime;
  updated_at: DateTime;
}
```

### User

```typescript
interface User {
  id: string;                    // UUID
  email: string;                 // Email único
  username: string;              // Username único
  full_name?: string;            // Nome completo
  role: 'admin' | 'editor' | 'viewer';
  is_active: boolean;
  is_verified: boolean;
  preferences: {                 // Preferências do usuário
    theme: 'light' | 'dark';
    palette: 'blue' | 'emerald' | 'violet' | 'rose' | 'amber';
  };
  created_at: DateTime;
  updated_at: DateTime;
}
```

## 🚀 Exemplos de Uso - Imagens

### Upload de Múltiplas Imagens

```javascript
// Upload de várias imagens de uma vez
const formData = new FormData();
formData.append('files', file1);
formData.append('files', file2);
formData.append('files', file3);

// Opcional: adicionar metadados
formData.append('metadata', JSON.stringify([
  { title: 'Imagem 1', display_time: 3000 },
  { title: 'Imagem 2', display_time: 5000 },
  { title: 'Imagem 3', display_time: 4000 }
]));

const response = await fetch(
  `http://localhost:8000/api/campaigns/${campaignId}/images`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  }
);

const uploadedImages = await response.json();
```

### Listar Imagens da Campanha

```javascript
const response = await fetch(
  `http://localhost:8000/api/campaigns/${campaignId}/images`,
  {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
);

const images = await response.json();
/*
[
  {
    "id": "uuid",
    "filename": "campaign_123_image_1.jpg",
    "url": "http://localhost:8000/static/uploads/campaign_123_image_1.jpg",
    "order_index": 0,
    "display_time": 5000,
    "title": "Promoção Principal",
    "size_bytes": 245789,
    "mime_type": "image/jpeg",
    "width": 1920,
    "height": 1080
  },
  ...
]
*/
```

### Reordenar Imagens

```javascript
// Nova ordem: array de IDs das imagens
await fetch(
  `http://localhost:8000/api/campaigns/${campaignId}/images/order`,
  {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      image_order: [imageId3, imageId1, imageId2] // Nova sequência
    })
  }
);
```

### Atualizar Dados de uma Imagem

```javascript
await fetch(
  `http://localhost:8000/api/images/${imageId}`,
  {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      title: 'Novo Título',
      description: 'Nova descrição',
      display_time: 7000,
      active: true
    })
  }
);
```

### Deletar Imagem

```javascript
await fetch(
  `http://localhost:8000/api/campaigns/${campaignId}/images/${imageId}`,
  {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
);
```

## 🎯 Sistema de Targeting Hierárquico

O sistema suporta 4 níveis de targeting para campanhas:

### Níveis de Targeting

1. **Global** - Campanha aparece em TODAS as estações
   ```json
   {
     "stations": [],
     "branches": [],
     "regions": []
   }
   ```

2. **Regional** - Campanha aparece em todas estações de uma região
   ```json
   {
     "regions": ["Norte", "Nordeste"],
     "branches": [],
     "stations": []
   }
   ```

3. **Por Filial** - Campanha aparece em todas estações de filiais específicas
   ```json
   {
     "branches": ["010101", "020202"],
     "stations": []
   }
   ```

4. **Por Estação** - Campanha aparece apenas em estações específicas
   ```json
   {
     "branches": ["010101"],
     "stations": ["001", "002"]
   }
   ```

### Regiões Disponíveis
- Norte
- Nordeste
- Centro-Oeste
- Sudeste
- Sul

## ⚠️ Regras de Negócio - Imagens

### Upload de Imagens

1. **Formatos aceitos**: 
   - JPEG/JPG
   - PNG
   - WEBP
   - GIF (estático)

2. **Limites**:
   - Tamanho máximo por arquivo: 10MB
   - Upload múltiplo: até 20 imagens por vez
   - Total por campanha: ilimitado

3. **Processamento**:
   - Redimensionamento automático se > 1920x1080
   - Otimização de qualidade (85% JPEG)
   - Geração de thumbnails (opcional)

4. **Ordenação**:
   - Índices sequenciais (0, 1, 2...)
   - Reordenação automática ao deletar
   - Drag & drop no frontend

5. **Display Time**:
   - Mínimo: 1000ms (1 segundo)
   - Máximo: 60000ms (60 segundos)
   - Padrão: 5000ms (5 segundos)
   - Override individual por imagem

### Validações de Upload

```javascript
// Validação no frontend antes do upload
function validateImage(file) {
  const maxSize = 10 * 1024 * 1024; // 10MB
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
  
  if (file.size > maxSize) {
    throw new Error('Arquivo muito grande (máx: 10MB)');
  }
  
  if (!allowedTypes.includes(file.type)) {
    throw new Error('Tipo de arquivo não permitido');
  }
  
  return true;
}
```

## 📱 Exemplo Completo - Fluxo de Criação de Campanha com Imagens

```javascript
class CampaignService {
  constructor(apiUrl, token) {
    this.apiUrl = apiUrl;
    this.token = token;
  }

  // 1. Criar campanha
  async createCampaign(campaignData) {
    const response = await fetch(`${this.apiUrl}/api/campaigns/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(campaignData)
    });
    return response.json();
  }

  // 2. Upload de imagens
  async uploadImages(campaignId, files, metadata = []) {
    const formData = new FormData();
    
    files.forEach(file => {
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
    return response.json();
  }

  // 3. Reordenar imagens
  async reorderImages(campaignId, imageIds) {
    const response = await fetch(
      `${this.apiUrl}/api/campaigns/${campaignId}/images/order`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ image_order: imageIds })
      }
    );
    return response.json();
  }

  // 4. Ativar campanha
  async activateCampaign(campaignId) {
    const response = await fetch(
      `${this.apiUrl}/api/campaigns/${campaignId}`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: 'active' })
      }
    );
    return response.json();
  }
}

// Uso
const service = new CampaignService('http://localhost:8000', token);

// Criar campanha completa
async function createCompleteCampaign() {
  // 1. Criar campanha
  const campaign = await service.createCampaign({
    name: 'Black Friday 2025',
    description: 'Promoções especiais de Black Friday',
    start_date: '2025-11-20T00:00:00Z',
    end_date: '2025-11-30T23:59:59Z',
    default_display_time: 5000,
    regions: ['Sudeste', 'Sul'], // Targeting regional
    priority: 90
  });

  // 2. Upload de imagens
  const files = [file1, file2, file3];
  const metadata = [
    { title: 'Banner Principal', display_time: 7000 },
    { title: 'Ofertas', display_time: 5000 },
    { title: 'Condições', display_time: 3000 }
  ];
  
  const images = await service.uploadImages(campaign.id, files, metadata);

  // 3. Reordenar se necessário
  const newOrder = images.map(img => img.id).reverse();
  await service.reorderImages(campaign.id, newOrder);

  // 4. Ativar campanha
  await service.activateCampaign(campaign.id);
  
  return campaign;
}
```

## 🔄 Paginação

Endpoints que suportam paginação:

```typescript
interface PaginatedResponse<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}
```

Parâmetros de query:
- `page`: Número da página (padrão: 1)
- `limit` ou `page_size`: Itens por página (padrão: 10, máx: 100)
- `sort_by`: Campo para ordenação
- `sort_order`: 'asc' ou 'desc'
- `search`: Busca textual

Exemplo:
```bash
GET /api/branches?page=1&limit=20&search=São Paulo&sort_by=name&sort_order=asc
```

## 🛡️ Segurança

### Headers Recomendados

```javascript
const headers = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${token}`,
  'X-Request-ID': generateUUID(), // Para tracking
  'Accept-Language': 'pt-BR',
  'X-Client-Version': '1.0.0'
};
```

### Tratamento de Erros

```javascript
async function apiRequest(url, options) {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const error = await response.json();
      
      switch (response.status) {
        case 401:
          // Token expirado - renovar
          await refreshToken();
          return apiRequest(url, options);
        case 403:
          // Sem permissão
          showError('Você não tem permissão para esta ação');
          break;
        case 422:
          // Erro de validação
          showValidationErrors(error.detail);
          break;
        default:
          showError(error.message || 'Erro desconhecido');
      }
      throw error;
    }
    
    return response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}
```

## 📊 Analytics e Métricas

### Dashboard Metrics

```javascript
// Obter métricas do dashboard
const metrics = await fetch('http://localhost:8000/api/metrics/dashboard', {
  headers: { 'Authorization': `Bearer ${token}` }
});

/*
Resposta:
{
  "overview": {
    "total_campaigns": 45,
    "total_active": 12,
    "total_images": 234,
    "total_users": 8
  },
  "recent_activity": {
    "last_7_days": 5,
    "last_30_days": 18
  },
  "top_priority_campaigns": [...]
}
*/
```

### Exportar Relatórios

```javascript
// Exportar para CSV
const csvData = await fetch(
  'http://localhost:8000/api/reports/export?format=csv&data_type=campaigns',
  {
    headers: { 'Authorization': `Bearer ${token}` }
  }
);

// Download do arquivo
const blob = await csvData.blob();
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'campaigns.csv';
a.click();
```

## 🧪 Testando a API

### Postman Collection

Importe a collection completa:
```
http://localhost:8000/openapi.json
```

### Testes Automatizados

```bash
# Rodar testes
pytest tests/

# Com coverage
pytest --cov=app tests/

# Testes específicos
pytest tests/test_images.py -v
```

### Exemplos cURL

```bash
# Upload de imagem única
curl -X POST "http://localhost:8000/api/campaigns/${CAMPAIGN_ID}/images" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "files=@image1.jpg"

# Upload múltiplo com metadata
curl -X POST "http://localhost:8000/api/campaigns/${CAMPAIGN_ID}/images" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F 'metadata=[{"title":"Imagem 1"},{"title":"Imagem 2"}]'

# Listar imagens
curl -X GET "http://localhost:8000/api/campaigns/${CAMPAIGN_ID}/images" \
  -H "Authorization: Bearer ${TOKEN}"

# Deletar imagem
curl -X DELETE "http://localhost:8000/api/campaigns/${CAMPAIGN_ID}/images/${IMAGE_ID}" \
  -H "Authorization: Bearer ${TOKEN}"
```

## 📱 Considerações para Frontend

### Upload de Imagens - UX Recomendada

1. **Drag & Drop**: Área para arrastar imagens
2. **Preview**: Mostrar miniaturas antes do upload
3. **Progress Bar**: Indicador de progresso individual
4. **Reordenação**: Drag & drop para reordenar
5. **Edição Inline**: Editar título e tempo de exibição
6. **Validação Visual**: Destacar erros (tamanho, formato)
7. **Bulk Actions**: Selecionar múltiplas para deletar

### Componente React Exemplo

```jsx
function ImageUploader({ campaignId }) {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState({});

  const handleDrop = (acceptedFiles) => {
    // Validar arquivos
    const validFiles = acceptedFiles.filter(file => {
      if (file.size > 10 * 1024 * 1024) {
        toast.error(`${file.name} é muito grande (máx: 10MB)`);
        return false;
      }
      return true;
    });
    
    setFiles(prev => [...prev, ...validFiles]);
  };

  const uploadImages = async () => {
    setUploading(true);
    const formData = new FormData();
    
    files.forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await fetch(
        `/api/campaigns/${campaignId}/images`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData,
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setProgress(percentCompleted);
          }
        }
      );
      
      if (response.ok) {
        toast.success('Imagens enviadas com sucesso!');
        setFiles([]);
      }
    } catch (error) {
      toast.error('Erro ao enviar imagens');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Dropzone onDrop={handleDrop} accept="image/*" maxSize={10485760}>
      {/* UI do dropzone */}
    </Dropzone>
  );
}
```

## 📞 Suporte e Contato

- **Projeto**: i9 Smart Campaigns
- **Versão API**: 1.0.0
- **Documentação Swagger**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI Schema**: `/openapi.json`

---

**Última atualização**: 25/01/2025
**Status**: API em produção
**Próximas features**: Websockets para notificações real-time, analytics avançado com IA