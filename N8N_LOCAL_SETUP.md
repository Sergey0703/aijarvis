# N8N Local Setup - Docker на Windows

## Цель
Запустить N8N локально в Docker на вашей машине для разработки и тестирования RSS парсинга.

---

## Prerequisites

- ✅ Docker Desktop для Windows (уже установлен?)
- ✅ Git (уже установлен)
- ✅ Текстовый редактор (VS Code)

---

## Step 1: Установка Docker Desktop (если нет)

### Проверка Docker:

```bash
docker --version
docker-compose --version
```

Если не установлен:
1. Скачать: https://www.docker.com/products/docker-desktop/
2. Установить
3. Запустить Docker Desktop
4. Убедиться что WSL2 включен (обычно автоматически)

---

## Step 2: Создать Docker Compose для N8N

### Создать файл `docker-compose.n8n.yml` в корне проекта:

```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n_local
    restart: unless-stopped
    ports:
      - "5678:5678"  # N8N UI
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=admin123  # Смени на свой!
      - N8N_HOST=localhost
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - WEBHOOK_URL=http://localhost:5678/
      - GENERIC_TIMEZONE=Europe/Moscow
    volumes:
      - n8n_data:/home/node/.n8n
      - ./n8n_workflows:/home/node/workflows  # Для экспорта/импорта workflows

volumes:
  n8n_data:
    driver: local
```

---

## Step 3: Запустить N8N

### В PowerShell/Command Prompt:

```bash
cd c:\projects\aijarvis

# Запустить N8N
docker-compose -f docker-compose.n8n.yml up -d

# Проверить что контейнер запущен
docker ps

# Посмотреть логи
docker-compose -f docker-compose.n8n.yml logs -f n8n
```

### Открыть N8N UI:

```
http://localhost:5678
```

**Логин:**
- Username: `admin`
- Password: `admin123`

---

## Step 4: Создать RSS Scraper Workflow

### В N8N UI (http://localhost:5678):

1. **Click "New Workflow"**
2. **Name:** `RSS News Scraper - Local`

### Добавить Nodes:

#### Node 1: Schedule Trigger
- **Тип:** Schedule Trigger
- **Mode:** Every X Hours
- **Hours:** 6
- **Name:** `Every 6 Hours`

#### Node 2: HTTP Request (TechCrunch)
- **Тип:** HTTP Request
- **Method:** GET
- **URL:** `https://techcrunch.com/feed/`
- **Response Format:** Text
- **Name:** `Fetch TechCrunch RSS`

#### Node 3: XML (Parse RSS)
- **Тип:** XML
- **Mode:** XML to JSON
- **Property Name:** `data`
- **Name:** `Parse XML`

#### Node 4: Item Lists (Split Items)
- **Тип:** Item Lists
- **Operation:** Split Out Items
- **Field to Split Out:** `rss.channel[0].item`
- **Name:** `Split Items`

#### Node 5: Code (Clean & Format)
- **Тип:** Code
- **Mode:** Run Once for All Items
- **JavaScript:**

```javascript
const items = $input.all();
const processed = [];

for (const item of items) {
  const data = item.json;

  // Extract fields
  const title = data.title?.[0] || 'No title';
  const description = data.description?.[0] || '';
  const link = data.link?.[0] || '';
  const pubDate = data.pubDate?.[0] || new Date().toISOString();

  // Clean HTML from description
  const cleanDescription = description
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .trim();

  // Limit length
  const summary = cleanDescription.length > 500
    ? cleanDescription.substring(0, 500) + '...'
    : cleanDescription;

  processed.push({
    json: {
      id: link,  // Use link as unique ID
      title: title,
      summary: summary,
      source: 'TechCrunch',
      rss_url: 'https://techcrunch.com/feed/',
      link: link,
      published_at: pubDate,
      created_at: new Date().toISOString(),
      used_count: 0,
      last_used_at: null,
      is_active: true
    }
  });
}

return processed;
```

#### Node 6: Spreadsheet File (Save to CSV)
- **Тип:** Spreadsheet File
- **Operation:** Write to file
- **File Format:** CSV
- **File Path:** `c:/projects/aijarvis/n8n_data/processed_news.csv`
- **Include Headers:** Yes
- **Columns:** Auto-detect

**Альтернатива (JSON):**

Вместо CSV можно использовать **Write Binary File**:
- **File Path:** `c:/projects/aijarvis/n8n_data/processed_news.json`
- **Binary Data:** `{{ JSON.stringify($json) }}`

---

## Step 5: Создать Webhook для Agent

### Новый Workflow: `Get Random News API - Local`

#### Node 1: Webhook
- **Тип:** Webhook
- **HTTP Method:** GET
- **Path:** `get-news`
- **Response Mode:** When Last Node Finishes
- **Name:** `Webhook Trigger`

**Webhook URL будет:** `http://localhost:5678/webhook/get-news`

#### Node 2: Read Binary File
- **Тип:** Read Binary Files
- **File Path:** `c:/projects/aijarvis/n8n_data/processed_news.json`
- **Name:** `Read Stored News`

#### Node 3: Code (Pick Random)
- **Тип:** Code
- **JavaScript:**

```javascript
// Parse JSON from file
const fileContent = $input.first().binary.data;
const newsArray = JSON.parse(fileContent.toString());

if (!newsArray || newsArray.length === 0) {
  return [{
    json: {
      error: 'No news available',
      fallback: true
    }
  }];
}

// Filter active news with low usage
const available = newsArray.filter(item =>
  item.is_active === true &&
  (item.used_count || 0) < 5
);

if (available.length === 0) {
  // Reset all to available
  newsArray.forEach(item => item.used_count = 0);
  available = newsArray;
}

// Pick random
const randomIndex = Math.floor(Math.random() * available.length);
const selected = available[randomIndex];

// Update usage
selected.used_count = (selected.used_count || 0) + 1;
selected.last_used_at = new Date().toISOString();

// Save back to file (simplified - в production нужно атомарно)
// Здесь просто возвращаем, обновление делаем в следующем node

return [{
  json: {
    selected: selected,
    allNews: newsArray  // Для сохранения обратно
  }
}];
```

#### Node 4: Write Binary File (Update Stats)
- **Тип:** Write Binary File
- **File Path:** `c:/projects/aijarvis/n8n_data/processed_news.json`
- **Binary Data:** `{{ JSON.stringify($json.allNews) }}`

#### Node 5: Respond to Webhook
- **Тип:** Respond to Webhook
- **Response Body:** `{{ $json.selected }}`
- **Response Code:** 200

---

## Step 6: Тестирование N8N Локально

### Test RSS Scraper:

1. В workflow "RSS News Scraper" нажать **"Execute Workflow"**
2. Проверить что создался файл: `c:/projects/aijarvis/n8n_data/processed_news.json`
3. Открыть файл - должен быть массив новостей

### Test Webhook:

1. Активировать workflow "Get Random News API"
2. В браузере открыть: `http://localhost:5678/webhook/get-news`
3. Должен вернуть JSON с одной новостью

**Или через PowerShell:**

```powershell
Invoke-WebRequest -Uri "http://localhost:5678/webhook/get-news" | Select-Object -ExpandProperty Content
```

---

## Step 7: Интеграция с Agent (Local Development)

### Проблема: Agent на HF Space не может достучаться до localhost

**Решение для разработки:**

#### Вариант A: ngrok (туннель)

1. Установить ngrok: https://ngrok.com/download
2. Запустить туннель:

```bash
ngrok http 5678
```

3. Получить публичный URL: `https://xxxx-xx-xx-xx-xx.ngrok-free.app`
4. Использовать в agent: `https://xxxx.ngrok-free.app/webhook/get-news`

#### Вариант B: Локальная разработка Agent

Вместо деплоя на HF Space, запускать agent локально:

```bash
cd c:\projects\aijarvis

# Set environment variables
set N8N_WEBHOOK_URL=http://localhost:5678/webhook/get-news
set LIVEKIT_URL=wss://first-aaelw7kf.livekit.cloud
set LIVEKIT_API_KEY=APICpeSck5jt2Rm
set LIVEKIT_API_SECRET=t4jZk0X3wGLvLAwh0d4iigxmrWLkrdEsmwe7FkDVYLT
set GOOGLE_API_KEY=ваш_ключ

# Run agent locally
python agent.py start
```

#### Вариант C: Deploy N8N к облачному провайдеру

Позже можем задеплоить N8N на Railway, Render или вашем VPS.

---

## Step 8: Update Agent для N8N Integration

Изменения уже описаны в `N8N_QUICKSTART.md` (добавить `requests`, функцию `fetch_news_from_n8n()`).

**Для локальной разработки используйте:**

```python
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/get-news")
```

---

## Управление N8N

### Остановить N8N:

```bash
docker-compose -f docker-compose.n8n.yml down
```

### Запустить снова:

```bash
docker-compose -f docker-compose.n8n.yml up -d
```

### Посмотреть логи:

```bash
docker-compose -f docker-compose.n8n.yml logs -f
```

### Backup workflows:

1. В N8N UI: Settings → Export Workflows
2. Сохранить JSON файлы в `c:/projects/aijarvis/n8n_workflows/`
3. Коммитить в Git

### Restore workflows:

1. В N8N UI: Import from File
2. Выбрать JSON файл из `n8n_workflows/`

---

## Данные и Persistence

**Где хранятся данные:**

- **N8N Database:** `Docker volume n8n_data` (workflows, credentials, executions)
- **Processed News:** `c:/projects/aijarvis/n8n_data/processed_news.json`

**Backup:**

```bash
# Backup N8N volume
docker run --rm -v n8n_data:/data -v c:/backup:/backup alpine tar czf /backup/n8n_backup.tar.gz /data

# Backup news data
copy c:\projects\aijarvis\n8n_data\processed_news.json c:\backup\
```

---

## Next Steps

1. ✅ Запустить N8N локально в Docker
2. ✅ Создать RSS Scraper workflow
3. ✅ Создать Webhook workflow
4. ✅ Тестировать локально
5. ⏭️ Добавить BBC и The Verge источники
6. ⏭️ Deploy N8N к облачному провайдеру (опционально)
7. ⏭️ Миграция с JSON файла на MongoDB (когда понадобится)

---

## Troubleshooting

### Docker не запускается:
- Убедись что Docker Desktop запущен
- Проверь WSL2: `wsl --status`

### N8N не открывается:
- Проверь порт: `netstat -ano | findstr :5678`
- Проверь логи: `docker logs n8n_local`

### Webhook не работает:
- Убедись что workflow активирован (есть галочка "Active")
- Проверь URL точно: `http://localhost:5678/webhook/get-news`

### Файл не создается:
- Проверь права доступа к папке `c:/projects/aijarvis/n8n_data/`
- Создай папку вручную: `mkdir c:\projects\aijarvis\n8n_data`

---

**Готовы начать? Запускаем Docker Compose!** 🐳
