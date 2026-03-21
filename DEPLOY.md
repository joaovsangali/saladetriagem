# Guia de Deploy Seguro — Sala de Triagem

Este documento descreve os procedimentos mínimos obrigatórios para colocar a plataforma em produção.

---

## 1. Variáveis de Ambiente Obrigatórias

Copie o template de produção e preencha os valores:

```bash
cp .env.production.example .env
```

As variáveis mínimas são:

```dotenv
# Gere com: python -c "import secrets; print(secrets.token_urlsafe(64))"
SECRET_KEY=<sua-chave-segura-aqui>

# Banco de dados PostgreSQL
DATABASE_URL=postgresql://triagem:<SENHA>@db:5432/triagem_db
POSTGRES_DB=triagem_db
POSTGRES_USER=triagem
POSTGRES_PASSWORD=<senha-forte>

# Redis
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
REDIS_PASSWORD=<senha-redis>

# Forçar HTTPS (True atrás de proxy com SSL)
FORCE_HTTPS=True
```

### Gerar SECRET_KEY segura

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

A chave deve ter **no mínimo 32 caracteres**. A aplicação recusará iniciar em modo produção com a chave padrão ou chaves curtas.

---

## 2. Configurar Armazenamento de Fotos (S3 ou local)

### Opção A: Storage Local (padrão, sem configuração extra)

```dotenv
STORAGE_BACKEND=local
UPLOAD_FOLDER=/var/app/uploads
```

As fotos são salvas no volume Docker `uploads`. Funciona sem nenhuma dependência externa, mas **não suporta múltiplas instâncias web** (cada instância teria seu próprio disco). Use para ambiente de desenvolvimento ou com uma única instância.

### Opção B: Storage S3 (recomendado para produção com múltiplos workers)

```dotenv
STORAGE_BACKEND=s3
S3_BUCKET=nome-do-bucket
S3_REGION=us-east-1
S3_ACCESS_KEY=<access-key-id>
S3_SECRET_KEY=<secret-access-key>
S3_ENDPOINT=             # vazio para AWS S3; para MinIO: https://minio.exemplo.com
S3_SIGNED_URL_TTL=3600   # validade das URLs assinadas (segundos)
```

#### Criar bucket na AWS

```bash
# Instale a CLI da AWS
pip install awscli
aws configure   # informe access key, secret key e região

# Criar bucket
aws s3 mb s3://nome-do-bucket --region us-east-1

# Bloquear acesso público (fotos são acessadas via signed URLs)
aws s3api put-public-access-block \
  --bucket nome-do-bucket \
  --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

#### Compatibilidade com MinIO (self-hosted)

```dotenv
STORAGE_BACKEND=s3
S3_BUCKET=triagem-fotos
S3_ENDPOINT=https://minio.seu-servidor.com
S3_REGION=us-east-1
S3_ACCESS_KEY=<minio-access-key>
S3_SECRET_KEY=<minio-secret-key>
```

#### Compatibilidade com dados antigos

Submissões criadas antes da migração para S3 continuam funcionando — as fotos que já estavam em memória/Redis permanecem acessíveis pela API. Novas submissões usarão o backend configurado.

---

## 3. Subir o Ambiente de Produção

### Construir a imagem

```bash
docker build -t saladetriagem:latest .
```

### Iniciar todos os serviços

```bash
docker-compose -f docker-compose.prod.yml up -d
```

Isso sobe: PostgreSQL, Redis, web (Gunicorn), worker (Celery), beat (Celery Beat) e nginx.

### Verificar que está funcionando

```bash
# Healthcheck via nginx (porta 80)
curl http://localhost/health

# Deve retornar: {"db": true, "status": "ok"}
```

---

## 4. Escalar Web Workers (Horizontal Scaling)

A aplicação é stateless: sessões e dados de submissão ficam no Redis; fotos vão para S3 ou volume compartilhado. Múltiplas instâncias web funcionam de forma transparente.

### Subir 3 instâncias web

```bash
docker-compose -f docker-compose.prod.yml up --scale web=3 -d
```

### Recarregar nginx para distribuir carga entre as novas instâncias

```bash
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### Verificar quantas instâncias estão rodando

```bash
docker-compose -f docker-compose.prod.yml ps web
```

### Voltar para 1 instância

```bash
docker-compose -f docker-compose.prod.yml up --scale web=1 -d
```

> **Nota sobre storage:** ao usar `--scale web=N` com `STORAGE_BACKEND=local`, todas as instâncias precisam montar o mesmo volume `uploads`. O `docker-compose.prod.yml` já faz isso via o volume compartilhado `uploads`. Para produção com múltiplos workers em hosts diferentes, use `STORAGE_BACKEND=s3`.

---

## 5. Load Balancer (Nginx)

O arquivo `nginx.conf` configura o Nginx como proxy reverso e load balancer.

### O que está configurado

- Upstream `web_backend` → `web:8000` (resolvido via DNS interno do Docker)
- `client_max_body_size 15m` (permite uploads de até 15 MB)
- Headers corretos: `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`
- Healthcheck: `GET /health`
- `proxy_request_buffering off` (uploads streamados, sem buffer no nginx)
- Conexões keepalive com os backends (melhor performance)

### Configurar HTTPS

Edite `nginx.conf` e descomente o bloco HTTPS:

```nginx
listen 443 ssl http2;
server_name YOURDOMAIN.example.com;

ssl_certificate     /etc/letsencrypt/live/YOURDOMAIN/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/YOURDOMAIN/privkey.pem;
ssl_protocols       TLSv1.2 TLSv1.3;
ssl_ciphers         HIGH:!aNULL:!MD5;
```

Adicione um bloco separado para redirecionar HTTP → HTTPS:

```nginx
server {
    listen 80;
    server_name YOURDOMAIN.example.com;
    return 301 https://$host$request_uri;
}
```

### Certificado Let's Encrypt (Certbot)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d YOURDOMAIN.example.com
```

---

## 6. Usando ProductionConfig

Para ativar todas as proteções de produção, use `ProductionConfig` ao iniciar:

```python
# run.py ou wsgi.py
from app import create_app
from config import ProductionConfig

app = create_app(ProductionConfig)
```

Ou via variável de ambiente com um entrypoint personalizado.

`ProductionConfig` ativa automaticamente:
- `SESSION_COOKIE_SECURE = True` (cookie só via HTTPS)
- `SESSION_COOKIE_HTTPONLY = True` (não acessível via JavaScript)
- `SESSION_COOKIE_SAMESITE = "Lax"` (proteção CSRF extra)
- `PERMANENT_SESSION_LIFETIME = 30 min`
- Validação obrigatória de `SECRET_KEY`

---

## 7. Audit Log (AccessLog)

Todos os acessos a triagens são registrados automaticamente na tabela `access_logs`.

Cada policial pode consultar seu próprio histórico em:

```
/dashboard/my-audit-log
```

### Retenção recomendada

- **Mínimo:** 90 dias
- Implemente um cron job mensal para limpar registros antigos:

```sql
DELETE FROM access_logs WHERE accessed_at < datetime('now', '-90 days');
```

---

## 8. Checklist de Segurança Pré-Deploy

- [ ] `SECRET_KEY` gerada e configurada (mín. 32 chars, nunca o valor default)
- [ ] `FORCE_HTTPS=True` configurado (atrás de proxy com SSL)
- [ ] Certificado SSL válido no servidor
- [ ] `DEBUG=False` (garantido pelo `ProductionConfig`)
- [ ] Banco de dados com permissões restritas
- [ ] Arquivo `.env` fora do repositório e sem permissão de leitura pública
- [ ] Backups do banco configurados
- [ ] Logs monitorados
- [ ] S3 bucket com acesso público bloqueado (fotos via signed URLs)

---

## 9. Validação Final

```bash
# 1. Healthcheck via nginx
curl http://localhost/health
# Esperado: {"db": true, "status": "ok"}

# 2. Verificar logs do nginx
docker-compose -f docker-compose.prod.yml logs nginx

# 3. Verificar logs da aplicação
docker-compose -f docker-compose.prod.yml logs web

# 4. Verificar workers Celery
docker-compose -f docker-compose.prod.yml logs worker

# 5. Testar upload de foto (substitua TOKEN pelo token real)
curl -X POST http://localhost/t/TOKEN/submit \
  -F "guest_name=Teste" \
  -F "crime_type=outros" \
  -F "photos=@/caminho/para/foto.jpg"
```

---

## 10. Rede Interna vs. Internet Pública

**Recomendação:** para uso em delegacias, prefira:

1. **Rede interna da delegacia** com Wi-Fi segmentado — menor superfície de ataque.
2. Se precisar de acesso externo: VPN obrigatória antes de acessar a aplicação.
3. Evite expor a porta 5000 diretamente; sempre use proxy reverso (Nginx).

---

## 11. Contato e Responsabilidade

Esta é uma ferramenta auxiliar, **não oficial**. Não substitui sistemas oficiais de registro de ocorrências. Dados tratados devem ser minimizados e descartados conforme a lógica de plantão implementada.
