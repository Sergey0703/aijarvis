# N8N Quick Start Guide - MVP v2

## Цель
Запустить базовую автоматизацию RSS парсинга с хранением в локальной таблице N8N за 1 день.

---

## Step-by-Step План (1 День)

### ⏰ Morning (2-3 часа): Setup N8N

#### 1. Создать N8N Cloud Account (10 минут)

1. Перейти на https://n8n.io/cloud
2. Sign Up (бесплатный tier: 5000 executions/month)
3. Создать новый Workspace: "English-Tutor-RSS"

#### 2. Создать Первый Workflow (1.5 часа)

**Workflow Name:** "RSS News Scraper - Simple"

**Nodes:**

```
[1] Cron Trigger
     ↓
[2] HTTP Request (TechCrunch RSS)
     ↓
[3] RSS Feed Read
     ↓
[4] Function (Clean HTML & Deduplicate)
     ↓
[5] Write to File / Google Sheets (temporary storage)
     ↓
[6] Done!
```

**Детальная Настройка:**

---

**Node 1: Cron Trigger**
- Name: `Every 6 Hours`
- Schedule: `0 */6 * * *` (00:00, 06:00, 12:00, 18:00 UTC)
- Active: Yes

---

**Node 2: HTTP Request**
- Name: `Fetch TechCrunch RSS`
- Method: GET
- URL: `https://techcrunch.com/feed/`
- Response Format: Text (XML)

---

**Node 3: RSS Feed Read**
- Name: `Parse RSS`
- Input: `{{ $json.data }}`
- Extract: All items

---

**Node 4: Function**
- Name: `Clean & Format`
- JavaScript Code:

```javascript
// Get current items
const items = $input.all();
const processedNews = [];

for (const item of items) {
  const title = item.json.title || 'No title';
  const summary = item.json.content || item.json.description || '';

  // Clean HTML tags
  const cleanSummary = summary.replace(/<[^>]+>/g, '').trim();

  // Limit length
  const shortSummary = cleanSummary.length > 500
    ? cleanSummary.substring(0, 500) + '...'
    : cleanSummary;

  processedNews.push({
    json: {
      id: item.json.guid || item.json.link,
      title: title,
      summary: shortSummary,
      source: 'TechCrunch',
      rss_url: 'https://techcrunch.com/feed/',
      link: item.json.link,
      published_at: item.json.pubDate || new Date().toISOString(),
      created_at: new Date().toISOString(),
      used_count: 0,
      is_active: true
    }
  });
}

return processedNews;
```

---

**Node 5: Google Sheets (Temporary Storage)**
- Name: `Save to Google Sheets`
- Operation: Append
- Spreadsheet: Create new "English-Tutor-News"
- Sheet: "processed_news"
- Columns:
  - id
  - title
  - summary
  - source
  - link
  - published_at
  - created_at
  - used_count

**Alternative (проще):** Use `Write Binary File` node и сохранить в JSON file на N8N сервере

---

#### 3. Test Workflow (30 минут)

1. Click "Execute Workflow" manually
2. Check каждый node:
   - HTTP Request должен вернуть XML
   - RSS Read должен распарсить items
   - Function должен очистить HTML
   - Google Sheets должен записать данные
3. Fix errors если есть
4. Activate Cron Trigger

---

### 🌆 Afternoon (2-3 часа): Agent Integration

#### 4. Создать N8N Webhook для Agent (1 час)

**New Workflow Name:** "Get Random News API"

**Nodes:**

```
[1] Webhook Trigger (GET /get-news)
     ↓
[2] Google Sheets: Read All News
     ↓
[3] Function: Pick Random Unused News
     ↓
[4] Google Sheets: Update used_count
     ↓
[5] Respond to Webhook (JSON)
```

**Детали:**

**Node 1: Webhook**
- Path: `/get-news`
- Method: GET
- Response Mode: When Last Node Finishes

**Node 2: Google Sheets Read**
- Operation: Read
- Sheet: "processed_news"
- Return All: Yes

**Node 3: Function - Pick Random**

```javascript
const items = $input.all()[0].json;

// Filter active news with low usage
const available = items.filter(item =>
  item.is_active === true &&
  (item.used_count || 0) < 5
);

if (available.length === 0) {
  // No news available
  return [{
    json: {
      error: "No news available",
      fallback: true
    }
  }];
}

// Pick random
const randomIndex = Math.floor(Math.random() * available.length);
const selectedNews = available[randomIndex];

return [{
  json: {
    id: selectedNews.id,
    title: selectedNews.title,
    summary: selectedNews.summary,
    source: selectedNews.source,
    link: selectedNews.link,
    published_at: selectedNews.published_at
  }
}];
```

**Node 4: Google Sheets Update**
- Operation: Update
- Sheet: "processed_news"
- Column to Match On: id
- Fields to Update:
  - used_count: `{{ $json.used_count + 1 }}`
  - last_used_at: `{{ new Date().toISOString() }}`

**Node 5: Respond**
- Response Body: `{{ $json }}`
- Response Code: 200

**Copy Webhook URL:** `https://xxx.app.n8n.cloud/webhook/get-news`

---

#### 5. Update agent.py (1 час)

**Добавить в agent.py:**

```python
import requests
import os

# N8N Webhook URL
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", None)

def fetch_news_from_n8n() -> dict:
    """
    Получает случайную новость из N8N workflow
    """
    if not N8N_WEBHOOK_URL:
        logger.warning("⚠️ N8N_WEBHOOK_URL не настроен, использую прямой RSS")
        return None

    try:
        logger.info("📡 Fetching news from N8N webhook...")
        response = requests.get(N8N_WEBHOOK_URL, timeout=10)

        if response.status_code == 200:
            news = response.json()

            if news.get('error'):
                logger.warning(f"⚠️ N8N returned error: {news['error']}")
                return None

            logger.info(f"✅ Got news from N8N: {news['title'][:50]}...")
            return news
        else:
            logger.error(f"❌ N8N webhook failed: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"❌ Failed to fetch from N8N: {e}")
        return None

# Modify entrypoint to use N8N first
async def entrypoint(ctx: JobContext):
    logger.info("🚀 Starting English Tutor Agent")

    # Try N8N first, fallback to direct RSS
    news = fetch_news_from_n8n()

    if not news:
        logger.info("📰 Falling back to direct RSS fetch")
        news = fetch_latest_news()

    lesson_text = format_lesson_from_news(news)
    # ... rest of code
```

---

#### 6. Update requirements.txt

```txt
# ---- HTTP CLIENT (для N8N webhook) ----
requests==2.32.3
```

---

#### 7. Add HF Spaces Secret

В Hugging Face Spaces Settings → Secrets:

```
N8N_WEBHOOK_URL=https://xxx.app.n8n.cloud/webhook/get-news
```

---

#### 8. Deploy & Test (30 минут)

```bash
git add agent.py requirements.txt
git commit -m "Add N8N webhook integration for news fetching"
git push github main
git push hf main
```

**Тестирование:**

1. Дождаться rebuild HF Space
2. Подключиться через LiveKit Playground
3. Проверить логи - должно быть `📡 Fetching news from N8N webhook...`
4. Услышать случайную новость из Google Sheets
5. Повторить подключение - должна быть другая новость

---

## Quick Troubleshooting

### N8N Webhook возвращает 404
- Проверь что workflow активирован
- Проверь URL (должен быть `/webhook/get-news`)

### Agent не может подключиться к N8N
- Проверь что `N8N_WEBHOOK_URL` добавлен в HF Secrets
- Проверь что `requests` добавлен в requirements.txt
- Проверь логи HF Space на наличие ошибок

### Google Sheets пустой
- Запусти RSS Scraper workflow вручную
- Проверь что credentials для Google правильные
- Проверь что sheet называется точно "processed_news"

---

## Next Steps (После Тестирования)

1. ✅ Работает базовый N8N парсинг + webhook
2. ⏭️ Добавить BBC и The Verge в RSS workflow
3. ⏭️ Миграция с Google Sheets на MongoDB
4. ⏭️ Добавить keyword extraction через OpenAI
5. ⏭️ Добавить difficulty assessment
6. ⏭️ Добавить translations для сложных слов

---

## Costs (Free Tier)

**N8N Cloud:**
- 5000 executions/month
- Наш use case: 4 runs/день (cron) + ~20 webhook calls/день = 720/месяц ✅

**Google Sheets:**
- Бесплатно ✅

**Total: $0**

---

## Migration Path: Google Sheets → MongoDB

Когда будем готовы:

1. Создать MongoDB Atlas аккаунт (бесплатный tier)
2. Создать database "english_tutor"
3. Создать collection "processed_news"
4. В N8N заменить Google Sheets nodes на MongoDB nodes
5. Migr existing data (export from Sheets → import to MongoDB)
6. Update agent.py (останется тот же webhook, ничего не меняется!)

**Преимущество:** Agent не знает где хранятся данные (Google Sheets или MongoDB) - он просто вызывает webhook!

---

**Готовы начать? Создаем N8N аккаунт!** 🚀
