# N8N Workflows для English Tutor

Эта папка содержит экспортированные N8N workflows для автоматизации RSS парсинга.

## Workflows

### 1. RSS News Scraper
- **Файл:** `rss_news_scraper.json`
- **Описание:** Парсит RSS из TechCrunch, BBC, The Verge каждые 6 часов
- **Trigger:** Schedule (cron)
- **Output:** `../n8n_data/processed_news.json`

### 2. Get Random News API
- **Файл:** `get_random_news_api.json`
- **Описание:** Webhook API для получения случайной новости
- **Endpoint:** `http://localhost:5678/webhook/get-news`
- **Method:** GET
- **Response:** JSON с одной новостью

## Как Импортировать

1. Открыть N8N UI: http://localhost:5678
2. Click "Import from File"
3. Выбрать `.json` файл из этой папки
4. Activate workflow

## Как Экспортировать (Backup)

1. В N8N UI открыть workflow
2. Click "..." → "Download"
3. Сохранить `.json` файл в эту папку
4. Commit в Git

## Заметки

- Файлы `.json` игнорируются Git (см. `.gitignore`)
- Это правильно, т.к. они могут содержать credentials
- Для бэкапа workflows используйте отдельный приватный репозиторий
