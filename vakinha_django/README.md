# Vakinha IA — Site Django de Doações

Plataforma completa de arrecadação coletiva com integração de IA via WhatsApp.

## Stack

- **Backend**: Django 5 + Django REST Framework
- **Banco de dados**: Neon (PostgreSQL serverless)
- **Cache / Broker**: Redis (Railway)
- **Tarefas assíncronas**: Celery
- **Pagamentos**: MercadoPago (PIX, cartão, boleto)
- **IA**: Agno + Google Gemini + Groq Whisper
- **WhatsApp**: Evolution API
- **Frontend**: Tailwind CSS via CDN
- **Deploy**: Railway

---

## Setup local

### 1. Criar ambiente virtual

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
```

### 2. Instalar dependências

```bash
pip install -r requirements/development.txt
```

### 3. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Edite .env com suas credenciais
```

### 4. Aplicar migrações

```bash
python manage.py migrate
```

### 5. Criar superusuário

```bash
python manage.py createsuperuser
```

### 6. Rodar o servidor

```bash
python manage.py runserver
```

Acesse: http://localhost:8000

### 7. Rodar Celery (para tarefas assíncronas)

```bash
celery -A config.celery worker --loglevel=info
```

---

## Deploy no Railway

### Variáveis de ambiente necessárias

| Variável | Descrição |
|----------|-----------|
| `SECRET_KEY` | Chave secreta Django (gere uma aleatória) |
| `DATABASE_URL` | Connection string do Neon (use o pooler, porta 6432) |
| `REDIS_URL` | URL do serviço Redis no Railway |
| `ALLOWED_HOSTS` | Domínio do Railway (ex: app.up.railway.app) |
| `SITE_URL` | URL completa do site (ex: https://app.up.railway.app) |
| `MERCADOPAGO_ACCESS_TOKEN` | Token de acesso MercadoPago |
| `MERCADOPAGO_PUBLIC_KEY` | Chave pública MercadoPago |
| `MERCADOPAGO_WEBHOOK_SECRET` | Secret para validar webhooks |
| `GEMINI_API_KEY` | Chave Google Gemini |
| `GROQ_API_KEY` | Chave Groq (Whisper) |
| `EVOLUTION_API_URL` | URL da Evolution API |
| `EVOLUTION_INSTANCE` | Nome da instância WhatsApp |
| `EVOLUTION_TOKEN` | Token da Evolution API |
| `AI_WEBHOOK_TOKEN` | Token secreto para o webhook da IA |
| `EMAIL_HOST_USER` | E-mail para envio de notificações |
| `EMAIL_HOST_PASSWORD` | Senha de app do Gmail |

### Passos

1. Crie um novo projeto no Railway
2. Adicione um serviço Redis
3. Conecte o repositório GitHub
4. Configure as variáveis de ambiente (acima)
5. O Railway detecta o `Procfile` e sobe `web` + `worker` automaticamente

### Webhook MercadoPago

Configure no painel do MercadoPago:
```
https://seudominio.railway.app/payments/webhook/
```

### Webhook WhatsApp (Evolution API)

Configure na Evolution API:
```
https://seudominio.railway.app/ai/webhook/<AI_WEBHOOK_TOKEN>/
```

---

## Estrutura do projeto

```
vakinha_django/
├── config/                  # Settings, URLs, Celery, WSGI
│   └── settings/
│       ├── base.py          # Configurações comuns
│       ├── development.py   # Dev (SQLite, email console)
│       └── production.py    # Prod (Neon, HTTPS, Sentry)
├── apps/
│   ├── accounts/            # Auth + perfil de usuário
│   ├── campaigns/           # Campanhas de doação
│   ├── payments/            # MercadoPago + webhook IPN
│   ├── dashboard/           # Métricas e analytics
│   ├── notifications/       # Email + WhatsApp (Celery)
│   └── ai_agent/            # Agente Gemini via WhatsApp
├── templates/               # Templates HTML (Tailwind)
├── static/                  # CSS e JS estáticos
└── requirements/
    ├── base.txt
    ├── development.txt
    └── production.txt
```
