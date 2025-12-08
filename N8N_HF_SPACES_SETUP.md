# N8N на Hugging Face Spaces - В том же Docker контейнере

## Проблема
Hugging Face Spaces поддерживает только **один основной процесс** в Docker контейнере. Нам нужно запустить **два сервиса**:
1. LiveKit Agent (Python) на порту 7860
2. N8N (Node.js) на порту 5678

## Решение: Supervisor (Process Manager)

Используем **supervisord** для управления несколькими процессами в одном контейнере.

---

## Архитектура

```
┌─────────────────────────────────────────────────────┐
│  Hugging Face Space Docker Container                │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  Supervisord (Process Manager)               │  │
│  │                                              │  │
│  │  ┌──────────────┐      ┌─────────────────┐  │  │
│  │  │ LiveKit      │      │ N8N             │  │  │
│  │  │ Agent        │      │ (Node.js)       │  │  │
│  │  │ (Python)     │      │                 │  │  │
│  │  │ Port: 7860   │      │ Port: 5678      │  │  │
│  │  └──────────────┘      └─────────────────┘  │  │
│  │                                              │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  EXPOSE 7860 (health check)                         │
└─────────────────────────────────────────────────────┘
```

---

## Обновленный Dockerfile

```dockerfile
# Multi-stage build для оптимизации размера
FROM node:18-slim AS n8n-builder

# Установить N8N
RUN npm install -g n8n

# --------------------------------------------------

FROM python:3.11-slim

# ========== SYSTEM DEPENDENCIES ==========
RUN apt-get update && apt-get install -y \
    # FFmpeg для аудио
    ffmpeg \
    libsndfile1 \
    # Supervisor для управления процессами
    supervisor \
    # Node.js для N8N
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# ========== INSTALL N8N ==========
RUN npm install -g n8n

# ========== WORKDIR ==========
WORKDIR /app

# ========== PYTHON DEPENDENCIES ==========
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ========== COPY APPLICATION ==========
COPY agent.py .

# ========== N8N SETUP ==========
# Create N8N directories
RUN mkdir -p /app/n8n_data /app/n8n_workflows

# Copy N8N workflows (if any)
COPY n8n_workflows/* /app/n8n_workflows/ || true

# ========== SUPERVISOR CONFIG ==========
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# ========== ENVIRONMENT ==========
ENV PYTHONUNBUFFERED=1
ENV N8N_BASIC_AUTH_ACTIVE=false
ENV N8N_PORT=5678
ENV N8N_HOST=0.0.0.0
ENV N8N_PROTOCOL=http
ENV WEBHOOK_URL=http://localhost:5678/

# ========== EXPOSE PORTS ==========
EXPOSE 7860

# ========== START SUPERVISOR ==========
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

---

## Supervisor Configuration

Создать файл `supervisord.conf`:

```ini
[supervisord]
nodaemon=true
logfile=/dev/stdout
logfile_maxbytes=0
loglevel=info

[program:n8n]
command=n8n start
directory=/app
autostart=true
autorestart=true
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
environment=N8N_USER_FOLDER="/app/n8n_data",N8N_PORT="5678",N8N_HOST="0.0.0.0"

[program:livekit-agent]
command=python agent.py start
directory=/app
autostart=true
autorestart=true
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
environment=N8N_WEBHOOK_URL="http://localhost:5678/webhook/get-news"
```

---

## Проблемы и Ограничения

### ❌ Проблема 1: N8N UI недоступен извне

**Почему:**
- HF Spaces пробрасывает только порт 7860
- N8N слушает на 5678 внутри контейнера
- Снаружи к N8N UI не подключиться

**Решение:**
- Настроить N8N workflows через JSON файлы (импорт при старте)
- Или использовать N8N headless mode (без UI)

### ❌ Проблема 2: Размер Docker образа

**Почему:**
- Python 3.11-slim: ~150 MB
- Node.js 18: ~200 MB
- N8N dependencies: ~300 MB
- Total: ~650 MB (может превысить лимиты HF)

**Решение:**
- Использовать alpine вместо slim (но сложнее с зависимостями)
- Или упростить N8N (только нужные nodes)

### ❌ Проблема 3: Persistent Storage

**Почему:**
- HF Spaces ephemeral storage (удаляется при рестарте)
- N8N workflows и данные теряются

**Решение:**
- Сохранять workflows в Git (n8n_workflows/)
- Использовать внешнее хранилище для данных (MongoDB, Supabase)

---

## Альтернативное Решение (Рекомендую)

### Вариант A: N8N на отдельном сервисе

**Архитектура:**

```
┌──────────────────────┐       ┌──────────────────────┐
│  HF Spaces           │       │  Railway/Render      │
│  (LiveKit Agent)     │◄──────│  (N8N)               │
│                      │ HTTP  │                      │
└──────────────────────┘       └──────────────────────┘
```

**Преимущества:**
- ✅ Разделение ответственности
- ✅ N8N UI доступен
- ✅ Легче обновлять и масштабировать
- ✅ Меньший размер Docker на HF

**Где запустить N8N:**

1. **Railway** (Рекомендую)
   - Free tier: $5 credit/month
   - 1-click deploy N8N
   - Persistent storage
   - URL: https://railway.app/

2. **Render**
   - Free tier (с ограничениями)
   - Docker support
   - URL: https://render.com/

3. **Fly.io**
   - Free tier: 3 VMs
   - Persistent volumes
   - URL: https://fly.io/

### Вариант B: N8N локально + ngrok

Запустить N8N локально (docker-compose) + ngrok для туннеля:

```bash
# Terminal 1: N8N
docker-compose -f docker-compose.n8n.yml up

# Terminal 2: ngrok
ngrok http 5678
```

**Webhook URL:** `https://xxxx.ngrok-free.app/webhook/get-news`

---

## Рекомендация

### Для Production: Вариант A (N8N на Railway)

**План:**

1. **Deploy N8N на Railway** (10 минут)
   - Sign up: https://railway.app/
   - New Project → Deploy N8N template
   - Получить URL: `https://your-n8n.railway.app`

2. **Настроить Workflows в N8N UI**
   - Создать RSS Scraper
   - Создать Webhook API
   - Экспортировать JSON (backup)

3. **Update Agent на HF Spaces**
   - Добавить Secret: `N8N_WEBHOOK_URL=https://your-n8n.railway.app/webhook/get-news`
   - Agent вызывает N8N через HTTP

**Costs:**
- Railway: $0 (free tier $5 credit покрывает N8N)
- HF Spaces: $0 (free tier)
- Total: $0

### Для Development: Вариант B (N8N локально + ngrok)

**План:**

1. Запустить N8N локально: `docker-compose -f docker-compose.n8n.yml up -d`
2. Запустить ngrok: `ngrok http 5678`
3. Использовать ngrok URL для тестирования
4. Когда готовы → мигрировать на Railway

---

## Next Steps

**Выберите вариант:**

### Хотите N8N в HF Spaces (сложнее, ограничения):
- ✅ Использую Dockerfile с Supervisor выше
- ❌ N8N UI недоступен извне
- ❌ Больший размер образа
- ❌ Данные не persistent

### Хотите N8N отдельно (проще, рекомендую):
- ✅ **Railway** - создать аккаунт, deploy N8N за 10 минут
- ✅ Или **Локально + ngrok** для разработки

**Что выбираем?**
