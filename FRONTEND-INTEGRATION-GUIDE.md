# 📱 Guia de Integração Frontend - i9 Smart Feed API

## 🚀 Início Rápido

### URLs Base
- **Produção**: `http://172.16.2.90:8000`
- **Documentação Swagger**: `http://172.16.2.90:8000/docs`
- **ReDoc**: `http://172.16.2.90:8000/redoc`

## 🔐 Autenticação

### 1. Login - Obter Token JWT

```javascript
// Exemplo JavaScript/TypeScript
async function login() {
  const response = await fetch('http://172.16.2.90:8000/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      username: 'adminuser',  // ou admin@i9smart.com
      password: 'Admin@123456'
    })
  });
  
  const data = await response.json();
  // Salvar o token
  localStorage.setItem('token', data.access_token);
  return data.access_token;
}
```

### 2. Usar Token nas Requisições

```javascript
// Adicionar token em todas as requisições autenticadas
const token = localStorage.getItem('token');

fetch('http://172.16.2.90:8000/api/campaigns', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

## 📋 Endpoints Principais

### Campanhas (Feeds)

#### Listar Campanhas
```javascript
async function listarCampanhas() {
  const response = await fetch('http://172.16.2.90:8000/api/campaigns', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return await response.json();
}
```

#### Criar Campanha
```javascript
async function criarCampanha() {
  const campanha = {
    name: "Promoção Janeiro 2025",
    description: "Ofertas especiais de janeiro",
    status: "active",
    start_date: "2025-01-22T00:00:00",
    end_date: "2025-01-31T23:59:59",
    default_display_time: 5000,  // 5 segundos
    stations: ["010101", "010102"]  // códigos das estações
  };
  
  const response = await fetch('http://172.16.2.90:8000/api/campaigns', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(campanha)
  });
  
  return await response.json();
}
```

#### Buscar Campanha Específica
```javascript
async function buscarCampanha(campaignId) {
  const response = await fetch(`http://172.16.2.90:8000/api/campaigns/${campaignId}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return await response.json();
}
```

### 🖼️ Upload de Imagens

#### Upload Simples
```javascript
async function uploadImagem(campaignId, file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`http://172.16.2.90:8000/api/campaigns/${campaignId}/images`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  const result = await response.json();
  console.log('Imagem enviada:', result);
  
  // A URL completa da imagem será:
  const imageUrl = `http://172.16.2.90:8000${result.url}`;
  console.log('URL da imagem:', imageUrl);
  
  return result;
}
```

#### Upload com Componente React
```jsx
function ImageUpload({ campaignId }) {
  const [uploading, setUploading] = useState(false);
  const [images, setImages] = useState([]);
  
  const handleUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    setUploading(true);
    try {
      const result = await uploadImagem(campaignId, file);
      // Construir URL completa
      const fullUrl = `http://172.16.2.90:8000${result.url}`;
      setImages([...images, { ...result, fullUrl }]);
    } catch (error) {
      console.error('Erro no upload:', error);
    } finally {
      setUploading(false);
    }
  };
  
  return (
    <div>
      <input 
        type="file" 
        accept="image/*" 
        onChange={handleUpload}
        disabled={uploading}
      />
      
      <div className="image-grid">
        {images.map(img => (
          <div key={img.id}>
            <img src={img.fullUrl} alt={img.original_filename} />
            <p>{img.original_filename}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 🏢 Filiais (Branches)

#### Listar Filiais
```javascript
async function listarFiliais() {
  const response = await fetch('http://172.16.2.90:8000/api/branches?limit=100', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return await response.json();
}

// Resposta esperada:
{
  "data": [
    {
      "code": "010101",
      "name": "MATRIZ",
      "active": true
    },
    {
      "code": "010102", 
      "name": "FILIAL 01",
      "active": true
    }
    // ... total de 32 filiais
  ],
  "total": 32,
  "page": 1,
  "pages": 1
}
```

### 🖥️ Estações (Stations)

#### Listar Estações
```javascript
async function listarEstacoes() {
  const response = await fetch('http://172.16.2.90:8000/api/stations?limit=100', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return await response.json();
}

// Resposta esperada:
{
  "data": [
    {
      "branch_code": "010101",
      "code": "001",
      "name": "POSTO 001",
      "status": "active"
    }
    // ... total de 480 estações
  ],
  "total": 480,
  "page": 1,
  "pages": 5
}
```

## 📱 Endpoint para Tablets (API Key)

### Buscar Campanhas Ativas
```javascript
// Para tablets/totems - usar API Key
async function getCampanhasTablet(stationCode) {
  const response = await fetch(`http://172.16.2.90:8000/api/stations/${stationCode}/active-campaigns`, {
    headers: {
      'X-API-Key': 'tablet_api_key_2025'  // API Key fornecida
    }
  });
  
  const data = await response.json();
  
  // Processar imagens com URLs completas
  data.campaigns.forEach(campaign => {
    campaign.images.forEach(image => {
      image.fullUrl = `http://172.16.2.90:8000${image.url}`;
    });
  });
  
  return data;
}
```

## 🎨 Exemplo de Componente Completo

```jsx
// CampaignManager.jsx
import React, { useState, useEffect } from 'react';

function CampaignManager() {
  const [token, setToken] = useState('');
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const baseUrl = 'http://172.16.2.90:8000';
  
  // Login automático ao carregar
  useEffect(() => {
    login();
  }, []);
  
  const login = async () => {
    try {
      const response = await fetch(`${baseUrl}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username: 'adminuser',
          password: 'Admin@123456'
        })
      });
      
      const data = await response.json();
      setToken(data.access_token);
      localStorage.setItem('token', data.access_token);
      
      // Carregar campanhas após login
      loadCampaigns(data.access_token);
    } catch (error) {
      console.error('Erro no login:', error);
    }
  };
  
  const loadCampaigns = async (authToken) => {
    try {
      const response = await fetch(`${baseUrl}/api/campaigns`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      const data = await response.json();
      setCampaigns(data.data || []);
    } catch (error) {
      console.error('Erro ao carregar campanhas:', error);
    }
  };
  
  const handleImageUpload = async (campaignId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch(`${baseUrl}/api/campaigns/${campaignId}/images`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      const result = await response.json();
      alert(`Imagem enviada! URL: ${baseUrl}${result.url}`);
      
      // Recarregar campanha para ver nova imagem
      loadCampaignDetails(campaignId);
    } catch (error) {
      console.error('Erro no upload:', error);
    }
  };
  
  const loadCampaignDetails = async (campaignId) => {
    try {
      const response = await fetch(`${baseUrl}/api/campaigns/${campaignId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      const data = await response.json();
      // Adicionar URLs completas às imagens
      if (data.images) {
        data.images = data.images.map(img => ({
          ...img,
          fullUrl: `${baseUrl}${img.url}`
        }));
      }
      setSelectedCampaign(data);
    } catch (error) {
      console.error('Erro ao carregar detalhes:', error);
    }
  };
  
  return (
    <div>
      <h1>Gerenciador de Campanhas</h1>
      
      {/* Lista de Campanhas */}
      <div>
        <h2>Campanhas</h2>
        <ul>
          {campaigns.map(campaign => (
            <li key={campaign.id}>
              <button onClick={() => loadCampaignDetails(campaign.id)}>
                {campaign.name} - {campaign.status}
              </button>
            </li>
          ))}
        </ul>
      </div>
      
      {/* Detalhes da Campanha Selecionada */}
      {selectedCampaign && (
        <div>
          <h2>{selectedCampaign.name}</h2>
          <p>{selectedCampaign.description}</p>
          
          {/* Upload de Imagem */}
          <input 
            type="file" 
            accept="image/*"
            onChange={(e) => {
              if (e.target.files[0]) {
                handleImageUpload(selectedCampaign.id, e.target.files[0]);
              }
            }}
          />
          
          {/* Galeria de Imagens */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
            {selectedCampaign.images?.map(img => (
              <div key={img.id}>
                <img 
                  src={img.fullUrl} 
                  alt={img.original_filename}
                  style={{ width: '100%', height: '200px', objectFit: 'cover' }}
                />
                <p>{img.original_filename}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default CampaignManager;
```

## 🧪 Script de Teste Completo

```html
<!-- test-api.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Teste API i9 Smart Feed</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        .section { margin: 20px 0; padding: 20px; border: 1px solid #ccc; }
        button { padding: 10px; margin: 5px; cursor: pointer; }
        .success { color: green; }
        .error { color: red; }
        img { max-width: 200px; margin: 10px; }
        #log { background: #f0f0f0; padding: 10px; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>Teste Completo da API i9 Smart Feed</h1>
    
    <div class="section">
        <h2>1. Login</h2>
        <button onclick="testLogin()">Fazer Login</button>
        <div id="loginResult"></div>
    </div>
    
    <div class="section">
        <h2>2. Campanhas</h2>
        <button onclick="testListCampaigns()">Listar Campanhas</button>
        <button onclick="testCreateCampaign()">Criar Campanha</button>
        <div id="campaignResult"></div>
    </div>
    
    <div class="section">
        <h2>3. Upload de Imagem</h2>
        <input type="file" id="imageFile" accept="image/*">
        <button onclick="testUploadImage()">Enviar Imagem</button>
        <div id="uploadResult"></div>
    </div>
    
    <div class="section">
        <h2>4. Filiais e Estações</h2>
        <button onclick="testBranches()">Listar Filiais</button>
        <button onclick="testStations()">Listar Estações</button>
        <div id="branchResult"></div>
    </div>
    
    <div class="section">
        <h2>5. Visualizar Imagens</h2>
        <button onclick="showCampaignImages()">Ver Imagens da Campanha</button>
        <div id="imageGallery"></div>
    </div>
    
    <div id="log">
        <h3>Log de Requisições</h3>
        <pre id="logContent"></pre>
    </div>
    
    <script>
        const baseUrl = 'http://172.16.2.90:8000';
        let token = '';
        let currentCampaignId = '';
        
        function log(message, isError = false) {
            const logEl = document.getElementById('logContent');
            const time = new Date().toLocaleTimeString();
            const color = isError ? 'red' : 'black';
            logEl.innerHTML += `<span style="color: ${color}">[${time}] ${message}</span>\n`;
        }
        
        async function testLogin() {
            try {
                log('Fazendo login...');
                const response = await fetch(`${baseUrl}/api/auth/login`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: new URLSearchParams({
                        username: 'adminuser',
                        password: 'Admin@123456'
                    })
                });
                
                const data = await response.json();
                token = data.access_token;
                localStorage.setItem('token', token);
                
                document.getElementById('loginResult').innerHTML = 
                    '<span class="success">✅ Login realizado com sucesso!</span>';
                log(`Token obtido: ${token.substring(0, 20)}...`);
            } catch (error) {
                document.getElementById('loginResult').innerHTML = 
                    '<span class="error">❌ Erro no login: ' + error.message + '</span>';
                log('Erro no login: ' + error.message, true);
            }
        }
        
        async function testListCampaigns() {
            try {
                log('Listando campanhas...');
                const response = await fetch(`${baseUrl}/api/campaigns`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                const data = await response.json();
                const campaigns = data.data || [];
                
                let html = '<h3>Campanhas Encontradas:</h3><ul>';
                campaigns.forEach(c => {
                    html += `<li>${c.name} (${c.status}) - ID: ${c.id}</li>`;
                    if (!currentCampaignId && c.status === 'active') {
                        currentCampaignId = c.id;
                    }
                });
                html += '</ul>';
                
                document.getElementById('campaignResult').innerHTML = html;
                log(`${campaigns.length} campanhas encontradas`);
            } catch (error) {
                document.getElementById('campaignResult').innerHTML = 
                    '<span class="error">❌ Erro: ' + error.message + '</span>';
                log('Erro ao listar campanhas: ' + error.message, true);
            }
        }
        
        async function testCreateCampaign() {
            try {
                log('Criando nova campanha...');
                const campaign = {
                    name: `Teste Frontend ${new Date().toLocaleTimeString()}`,
                    description: "Campanha criada pelo teste frontend",
                    status: "active",
                    start_date: new Date().toISOString(),
                    end_date: new Date(Date.now() + 7*24*60*60*1000).toISOString(),
                    default_display_time: 5000,
                    stations: ["010101"]
                };
                
                const response = await fetch(`${baseUrl}/api/campaigns`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(campaign)
                });
                
                const data = await response.json();
                currentCampaignId = data.id;
                
                document.getElementById('campaignResult').innerHTML = 
                    `<span class="success">✅ Campanha criada! ID: ${data.id}</span>`;
                log(`Campanha criada com ID: ${data.id}`);
            } catch (error) {
                document.getElementById('campaignResult').innerHTML = 
                    '<span class="error">❌ Erro: ' + error.message + '</span>';
                log('Erro ao criar campanha: ' + error.message, true);
            }
        }
        
        async function testUploadImage() {
            const fileInput = document.getElementById('imageFile');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('Selecione uma imagem primeiro!');
                return;
            }
            
            if (!currentCampaignId) {
                alert('Crie ou selecione uma campanha primeiro!');
                return;
            }
            
            try {
                log(`Enviando imagem ${file.name}...`);
                const formData = new FormData();
                formData.append('file', file);
                
                const response = await fetch(`${baseUrl}/api/campaigns/${currentCampaignId}/images`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    },
                    body: formData
                });
                
                const data = await response.json();
                const fullUrl = `${baseUrl}${data.url}`;
                
                document.getElementById('uploadResult').innerHTML = 
                    `<span class="success">✅ Imagem enviada!</span><br>
                     <img src="${fullUrl}" alt="Uploaded image">`;
                log(`Imagem enviada: ${fullUrl}`);
            } catch (error) {
                document.getElementById('uploadResult').innerHTML = 
                    '<span class="error">❌ Erro: ' + error.message + '</span>';
                log('Erro no upload: ' + error.message, true);
            }
        }
        
        async function testBranches() {
            try {
                log('Listando filiais...');
                const response = await fetch(`${baseUrl}/api/branches?limit=5`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                const data = await response.json();
                const branches = data.data || [];
                
                let html = `<h3>Filiais (${data.total} total):</h3><ul>`;
                branches.forEach(b => {
                    html += `<li>${b.code} - ${b.name}</li>`;
                });
                html += '</ul>';
                
                document.getElementById('branchResult').innerHTML = html;
                log(`${data.total} filiais disponíveis`);
            } catch (error) {
                document.getElementById('branchResult').innerHTML = 
                    '<span class="error">❌ Erro: ' + error.message + '</span>';
                log('Erro ao listar filiais: ' + error.message, true);
            }
        }
        
        async function testStations() {
            try {
                log('Listando estações...');
                const response = await fetch(`${baseUrl}/api/stations?limit=5`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                const data = await response.json();
                const stations = data.data || [];
                
                let html = `<h3>Estações (${data.total} total):</h3><ul>`;
                stations.forEach(s => {
                    html += `<li>${s.branch_code}/${s.code} - ${s.name}</li>`;
                });
                html += '</ul>';
                
                document.getElementById('branchResult').innerHTML += html;
                log(`${data.total} estações disponíveis`);
            } catch (error) {
                document.getElementById('branchResult').innerHTML += 
                    '<span class="error">❌ Erro: ' + error.message + '</span>';
                log('Erro ao listar estações: ' + error.message, true);
            }
        }
        
        async function showCampaignImages() {
            if (!currentCampaignId) {
                alert('Selecione uma campanha primeiro!');
                return;
            }
            
            try {
                log(`Carregando imagens da campanha ${currentCampaignId}...`);
                const response = await fetch(`${baseUrl}/api/campaigns/${currentCampaignId}`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                const campaign = await response.json();
                const images = campaign.images || [];
                
                let html = `<h3>Imagens da Campanha "${campaign.name}":</h3>`;
                if (images.length === 0) {
                    html += '<p>Nenhuma imagem encontrada</p>';
                } else {
                    html += '<div style="display: flex; flex-wrap: wrap;">';
                    images.forEach(img => {
                        const fullUrl = `${baseUrl}${img.url}`;
                        html += `
                            <div style="margin: 10px;">
                                <img src="${fullUrl}" alt="${img.original_filename}">
                                <p>${img.original_filename}</p>
                            </div>
                        `;
                    });
                    html += '</div>';
                }
                
                document.getElementById('imageGallery').innerHTML = html;
                log(`${images.length} imagens encontradas`);
            } catch (error) {
                document.getElementById('imageGallery').innerHTML = 
                    '<span class="error">❌ Erro: ' + error.message + '</span>';
                log('Erro ao carregar imagens: ' + error.message, true);
            }
        }
        
        // Auto-login ao carregar
        window.onload = () => {
            log('Página carregada. Clique em "Fazer Login" para começar.');
        };
    </script>
</body>
</html>
```

## ❗ Troubleshooting

### Problema: Token expirado
**Solução**: Fazer novo login. Token expira em 24 horas.

### Problema: Imagem não aparece
**Verificar**:
1. Upload retornou sucesso (200)?
2. URL está completa? (`http://172.16.2.90:8000` + `/static/uploads/...`)
3. Imagem está no formato correto? (jpg, png, webp)

### Problema: CORS bloqueado
**Solução**: 
- Para desenvolvimento, usar proxy no frontend
- Ou adicionar origem no backend (`CORS_ORIGINS`)

### Problema: Campanha não aparece no tablet
**Verificar**:
1. Status da campanha é "active"?
2. Data atual está entre start_date e end_date?
3. Station está associada à campanha?

## 📞 Suporte

Para dúvidas técnicas sobre a API:
- Swagger UI: http://172.16.2.90:8000/docs
- Logs do container: `docker logs i9-feed-api`
- Verificar saúde: `curl http://172.16.2.90:8000/health`

## 🎯 Checklist de Integração

- [ ] Consegue fazer login e obter token
- [ ] Token é salvo e usado nas requisições
- [ ] Lista campanhas corretamente
- [ ] Cria nova campanha
- [ ] Faz upload de imagem
- [ ] Visualiza imagens com URL completa
- [ ] Lista filiais e estações
- [ ] Trata erros adequadamente
- [ ] Implementa refresh de token (quando expirar)
- [ ] Mostra feedback visual durante operações

---

**Atualizado em**: 22/01/2025
**API Version**: 1.0.0
**Status**: ✅ Produção