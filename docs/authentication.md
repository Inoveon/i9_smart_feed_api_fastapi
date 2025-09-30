# Autenticação

- Login JWT: `POST /api/auth/login` (x-www-form-urlencoded: username, password)
- Refresh: `POST /api/auth/refresh` (JSON: { "refresh_token": "..." })
- Tablets (somente leitura): Header `X-API-Key: i9smart_campaigns_readonly_2025`
- Perfis: admin, editor, viewer (campo `role` do usuário)
