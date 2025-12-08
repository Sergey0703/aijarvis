# План Интеграции N8N для Обработки Новостей

## Цель
Автоматизировать процесс получения, обработки и подготовки новостей для уроков английского языка.

---

## Текущее Состояние (MVP v1)

```
[HF Space Agent]
    ├─ Fetches RSS при каждом подключении
    ├─ Парсит первую новость
    ├─ Очищает HTML
    └─ Читает пользователю
```

**Ограничения:**
- ❌ Парсинг RSS при каждом подключении (медленно)
- ❌ Нет истории новостей
- ❌ Нет персонализации
- ❌ Нет обработки текста (извлечение ключевых слов, перевод сложных терминов)
- ❌ Всегда одна и та же новость для всех пользователей

---

## Целевая Архитектура (MVP v2 с N8N)

```
┌─────────────────────────────────────────────────────────────┐
│                        N8N Workflow                         │
│  (Cloud или Self-hosted)                                    │
│                                                             │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐           │
│  │ RSS Cron │────>│ Process  │────>│ Store to │           │
│  │(каждые   │     │ News     │     │ Database │           │
│  │ 6 часов) │     │          │     │          │           │
│  └──────────┘     └──────────┘     └──────────┘           │
│                         │                                   │
│                    Extract:                                 │
│                    - Keywords                               │
│                    - Difficulty                             │
│                    - Translate terms                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    ┌───────────────┐
                    │   Database    │
                    │  (Supabase)   │
                    └───────────────┘
                            ↑
┌─────────────────────────────────────────────────────────────┐
│              HF Space - LiveKit Agent                       │
│                                                             │
│  При подключении:                                           │
│  1. Читает обработанную новость из DB                       │
│  2. Берет keywords, translations                            │
│  3. Формирует урок                                          │
│  4. Обсуждает с пользователем                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Этапы Реализации

### Phase 1: Инфраструктура (Неделя 1)

#### 1.1 Выбор и Настройка N8N
**Варианты:**
- [ ] **N8N Cloud** (рекомендую для старта)
  - ✅ Быстрый старт, бесплатный tier
  - ✅ Управляемый хостинг
  - ❌ Лимиты на бесплатном плане

- [ ] **Self-hosted N8N на Railway/Render**
  - ✅ Больше контроля
  - ✅ Можно использовать Docker
  - ❌ Нужно настраивать инфраструктуру

**Решение:** N8N Cloud для MVP

#### 1.2 Выбор Базы Данных

**Phase 1 (MVP v2): Локальная таблица N8N**
- ✅ Встроенная в N8N (SQLite)
- ✅ Не требует дополнительной инфраструктуры
- ✅ Идеально для старта и тестирования
- ❌ Ограничена объемом N8N instance

**Phase 2 (Future): MongoDB**
- ✅ Гибкая схема
- ✅ Бесплатный tier (Atlas 512MB)
- ✅ Легко масштабируется
- ✅ N8N native integration

**Решение для старта:** Локальная таблица N8N → потом миграция на MongoDB

**N8N Local Table Schema (Simplified):**

В N8N будем хранить данные в формате JSON через workflow переменные:

```json
{
  "id": "uuid-v4",
  "title": "News title",
  "summary": "News summary (cleaned)",
  "source": "TechCrunch",
  "rss_url": "https://techcrunch.com/feed/",
  "published_at": "2025-12-08T10:00:00Z",
  "created_at": "2025-12-08T10:05:00Z",

  // Обработанные данные (пока без keywords)
  "used_count": 0,
  "last_used_at": null,
  "is_active": true
}
```

**Когда перейдем на MongoDB - добавим:**
```json
{
  "keywords": ["AI", "workplace", "automation"],
  "difficulty_level": "intermediate",
  "translations": {
    "augment": "дополнять, усиливать",
    "capabilities": "способности, возможности"
  }
}
```

---

### Phase 2: N8N Workflow (Неделя 1-2)

#### 2.1 Workflow: RSS Parser & Processor

**Nodes:**
1. **Cron Trigger** (каждые 6 часов)
2. **HTTP Request** (3 parallel) → Fetch RSS от TechCrunch, BBC, The Verge
3. **RSS Feed Read** → Parse XML
4. **Function** → Deduplicate (проверка что новость еще не обработана)
5. **OpenAI** или **Claude API** → Extract keywords, assess difficulty
6. **Google Translate API** → Translate сложные термины
7. **Supabase Insert** → Save to database
8. **Telegram/Email** (optional) → Notify об ошибках

**N8N Workflow JSON (черновик):**
```json
{
  "name": "RSS News Processor",
  "nodes": [
    {
      "name": "Cron Trigger",
      "type": "n8n-nodes-base.cron",
      "position": [250, 300],
      "parameters": {
        "triggerTimes": {
          "item": [
            {
              "mode": "everyX",
              "value": 6,
              "unit": "hours"
            }
          ]
        }
      }
    },
    {
      "name": "Fetch TechCrunch",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 200],
      "parameters": {
        "url": "https://techcrunch.com/feed/",
        "responseFormat": "text"
      }
    }
    // ... и т.д.
  ]
}
```

#### 2.2 Workflow: Cleanup Old News

**Nodes:**
1. **Cron Trigger** (раз в день)
2. **Supabase Query** → SELECT news older than 7 days
3. **Supabase Update** → SET is_active = FALSE

---

### Phase 3: Agent Integration (Неделя 2)

#### 3.1 Добавить Supabase Client в Agent

**Изменения в agent.py:**

```python
# requirements.txt
supabase==2.10.0

# agent.py
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_news_from_db(difficulty: str = "intermediate") -> dict:
    """
    Получает случайную обработанную новость из Supabase
    """
    response = supabase.table('processed_news')\
        .select('*')\
        .eq('is_active', True)\
        .eq('difficulty_level', difficulty)\
        .order('used_count', desc=False)\
        .limit(1)\
        .execute()

    if response.data:
        news = response.data[0]
        # Update usage stats
        supabase.table('processed_news')\
            .update({
                'used_count': news['used_count'] + 1,
                'last_used_at': 'NOW()'
            })\
            .eq('id', news['id'])\
            .execute()
        return news
    return None
```

#### 3.2 Обновить Lesson Formatting

```python
def format_lesson_from_processed_news(news: dict) -> str:
    """
    Форматирует обработанную новость в текст урока с ключевыми словами
    """
    keywords_str = ", ".join(news['keywords'][:5])

    lesson_text = f"""
Welcome to your English practice.

Today's news from {news['source']}: {news['title']}

{news['summary']}

Key vocabulary to focus on: {keywords_str}

I am ready to discuss this article with you.
Let's practice using these new words in our conversation!
"""
    return lesson_text
```

---

### Phase 4: N8N Webhook для Динамических Запросов (Опционально)

**Use case:** Agent запрашивает новость определенной сложности или темы

**N8N Webhook Workflow:**
1. **Webhook Trigger** → POST /get-news
2. **Function** → Parse request (difficulty, topic)
3. **Supabase Query** → Filter by params
4. **Respond to Webhook** → Return JSON

**Agent изменения:**
```python
import requests

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

def fetch_news_via_n8n(difficulty: str = "intermediate") -> dict:
    """
    Запрашивает новость через N8N webhook
    """
    response = requests.post(N8N_WEBHOOK_URL, json={
        "difficulty": difficulty,
        "topic": "technology"
    })
    return response.json()
```

---

## Переменные Окружения (Секреты)

**Hugging Face Spaces Secrets (добавить):**
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
N8N_WEBHOOK_URL=https://xxx.app.n8n.cloud/webhook/...  # опционально
```

**N8N Environment Variables:**
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGc...  # service role key для write доступа
OPENAI_API_KEY=sk-...  # для извлечения keywords
GOOGLE_TRANSLATE_API_KEY=...  # опционально
```

---

## Roadmap

### Week 1: Foundation
- [ ] День 1-2: Создать Supabase проект, настроить таблицы
- [ ] День 3-4: Создать N8N Cloud аккаунт, базовый RSS workflow
- [ ] День 5: Тестировать workflow, заполнить DB тестовыми данными

### Week 2: Integration
- [ ] День 1-2: Добавить Supabase клиент в agent.py
- [ ] День 3: Обновить lesson formatting с keywords
- [ ] День 4: Тестирование end-to-end
- [ ] День 5: Deploy и мониторинг

### Week 3: Enhancement (Опционально)
- [ ] Webhook для динамических запросов
- [ ] Персонализация по уровню пользователя
- [ ] История уроков пользователя

---

## Costs Estimate (Free Tier)

**N8N Cloud:**
- Free tier: 5,000 workflow executions/month
- Наш use case: 4 запуска/день × 30 дней = 120 executions ✅

**Supabase:**
- Free tier: 500MB DB, 2GB bandwidth, 50,000 requests/month
- Наш use case: ~1000 news × 5KB = 5MB, ~100 requests/день = 3000/месяц ✅

**OpenAI API (для keyword extraction):**
- GPT-4o-mini: $0.15/1M input tokens
- ~500 tokens/новость × 120 новостей/месяц = 60,000 tokens = $0.01/месяц ✅

**Total: $0 (все в пределах free tier)**

---

## Альтернативный Подход (Проще, но менее мощный)

Если N8N кажется избыточным:

**Вариант B: Scheduled Python Script на GitHub Actions**

```yaml
# .github/workflows/process_news.yml
name: Process RSS News

on:
  schedule:
    - cron: '0 */6 * * *'  # каждые 6 часов

jobs:
  process:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
      - name: Run processor
        run: python scripts/process_news.py
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

**Pros:**
- ✅ Бесплатно (GitHub Actions)
- ✅ Версионируется в Git
- ✅ Проще для разработчиков

**Cons:**
- ❌ Меньше визуализации
- ❌ Нет UI для non-developers
- ❌ Сложнее отлаживать

---

## Рекомендация

**Для MVP v2 рекомендую:**
1. **Phase 1 + Phase 2** с N8N Cloud + Supabase
2. **Phase 3** интеграция в agent
3. **Отложить Phase 4** (webhook) до v3

**Преимущества:**
- Визуальный workflow (легко показать, легко изменить)
- Быстрая итерация без деплоя кода
- Готовая инфраструктура для будущих фич

**Начать с:**
1. Создать Supabase проект (10 минут)
2. Создать N8N Cloud аккаунт (5 минут)
3. Собрать простейший workflow: RSS → Supabase (1-2 часа)
4. Протестировать на 1 источнике
5. Расширять постепенно

---

## Вопросы для Уточнения

1. **Хотите начать с N8N или GitHub Actions подходом?**
2. **Нужна ли персонализация по уровню пользователя сразу или в v3?**
3. **Какие еще обработки новостей нужны кроме keywords и difficulty?**
   - Перевод всего текста?
   - Генерация вопросов для обсуждения?
   - Подмена простых слов на сложные из словаря?

Готов начать с Phase 1 когда скажете!
