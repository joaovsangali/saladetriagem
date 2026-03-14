# Guia de Deploy Seguro — Sala de Triagem

Este documento descreve os procedimentos mínimos obrigatórios para colocar a plataforma em produção.

---

## 1. Variáveis de Ambiente Obrigatórias

Crie um arquivo `.env.production` (nunca versione este arquivo) com as seguintes variáveis:

```dotenv
# Gere com: python -c "import secrets; print(secrets.token_urlsafe(64))"
SECRET_KEY=<sua-chave-segura-aqui>

# Banco de dados (SQLite para volume pequeno, PostgreSQL para maior)
DATABASE_URL=sqlite:////caminho/absoluto/triagem.db

# Forçar HTTPS (defina como True atrás de proxy reverso)
FORCE_HTTPS=True

# E-mail (opcional; se vazio, links de confirmação aparecem no console)
SMTP_HOST=smtp.seu-provedor.com
SMTP_PORT=587
SMTP_USER=usuario@exemplo.com
SMTP_PASSWORD=sua-senha-smtp
SMTP_USE_TLS=True
MAIL_FROM=noreply@exemplo.com
```

### Gerar SECRET_KEY segura

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

A chave deve ter **no mínimo 32 caracteres**. A aplicação recusará iniciar em modo produção com a chave padrão ou chaves curtas.

---

## 2. Usando ProductionConfig

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

## 3. Configuração Nginx com SSL

```nginx
server {
    listen 80;
    server_name sala.delegacia.exemplo.br;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name sala.delegacia.exemplo.br;

    ssl_certificate     /etc/letsencrypt/live/sala.delegacia.exemplo.br/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sala.delegacia.exemplo.br/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 4. Configuração Caddy (HTTPS automático)

```caddyfile
sala.delegacia.exemplo.br {
    reverse_proxy 127.0.0.1:5000
}
```

O Caddy obtém e renova automaticamente certificados Let's Encrypt.

---

## 5. Certificado Let's Encrypt (Certbot)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d sala.delegacia.exemplo.br
```

---

## 6. Iniciando com Gunicorn

```bash
pip install gunicorn
gunicorn -w 2 -b 127.0.0.1:5000 "app:create_app('config.ProductionConfig')"
```

Ou com módulo:

```bash
gunicorn -w 2 -b 127.0.0.1:5000 run:app
```

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
- [ ] Arquivo `.env.production` fora do repositório e sem permissão de leitura pública
- [ ] Backups do banco configurados
- [ ] Logs monitorados

---

## 9. Rede Interna vs. Internet Pública

**Recomendação:** para uso em delegacias, prefira:

1. **Rede interna da delegacia** com Wi-Fi segmentado — menor superfície de ataque.
2. Se precisar de acesso externo: VPN obrigatória antes de acessar a aplicação.
3. Evite expor a porta 5000 diretamente; sempre use proxy reverso (Nginx/Caddy).

---

## 10. Contato e Responsabilidade

Esta é uma ferramenta auxiliar, **não oficial**. Não substitui sistemas oficiais de registro de ocorrências. Dados tratados devem ser minimizados e descartados conforme a lógica de plantão implementada.
