# Checklist de Segurança Pós-Deploy

## ⚠️ OBRIGATÓRIO ANTES DE PRODUÇÃO

### 1. Remover .env do repositório
```bash
git rm --cached .env
git add .gitignore
git commit -m "Remove .env from repo and update .gitignore"
git push
```

### 2. Rotacionar TODAS as secrets
```bash
# Gerar novas secrets
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))")
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

# Atualizar no servidor (via SSH, variáveis de ambiente, etc)
```

### 3. Configurar S3
```bash
# Criar bucket
aws s3 mb s3://saladetriagem-fotos --region us-east-1

# Criar usuário IAM
aws iam create-user --user-name saladetriagem-app

# Criar policy e anexar ao usuário
# (ver documentação completa em DEPLOY.md)

# Atualizar .env no servidor:
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET=saladetriagem-fotos
S3_REGION=us-east-1
```

### 4. Ativar HTTPS
```bash
# Opção A: Certbot (Let's Encrypt)
sudo certbot --nginx -d seudominio.com

# Opção B: Manual (descomente seção HTTPS no nginx.conf)
```

### 5. Configurar variáveis de ambiente produção
```bash
FLASK_ENV=production
FORCE_HTTPS=True
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

### 6. Rodar migrations
```bash
docker-compose -f docker-compose.prod.yml exec web flask db upgrade
```

### 7. Testar health check
```bash
curl https://seudominio.com/health
# Deve retornar: {"status":"ok","db":true,"redis":true,"s3":true}
```

### 8. Verificar Celery
```bash
docker-compose -f docker-compose.prod.yml logs -f worker
docker-compose -f docker-compose.prod.yml logs -f beat

# Deve mostrar tasks rodando sem erros
```

## 📋 CHECKLIST

- [ ] `.env` removido do repo
- [ ] Secrets rotacionadas
- [ ] S3 configurado e testado
- [ ] HTTPS ativo
- [ ] Health check retorna OK
- [ ] Celery worker + beat rodando
- [ ] Teste completo: criar plantão → enviar formulário → fechar → verificar fotos deletadas
- [ ] Monitoramento configurado (Prometheus/Grafana opcional)
