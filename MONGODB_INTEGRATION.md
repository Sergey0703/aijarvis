# MongoDB Integration - Словарь пользователя

## Обзор

Интеграция с MongoDB Atlas для хранения и управления словарём английских слов пользователя.

---

## Структура данных

### Database: `cluster0`
### Collection: `words`

**Пример документа:**

```json
{
  "_id": ObjectId("61926d20f5f17d36c4aae9da"),
  "word": "epilraph",
  "translate": "эпиграф",
  "transcript": "ˈepɪɡrɑːf",
  "code": "YYIptx78Fa",
  "owner": "56ff68a8c0db3db578b86d622",
  "link": "https://audiocdn.lingualeo.com/v2/3/240a233b9cGE8a4f3c7c.mp3",
  "traini": true,
  "trainDate": "2024-03-06T14:24:10.631+00:00",
  "updateDate": "2021-11-15T14:22:24.413+00:00",
  "__v": 0
}
```

**Поля:**

| Поле | Тип | Описание |
|------|-----|----------|
| `_id` | ObjectId | Уникальный ID документа |
| `word` | String | Английское слово |
| `translate` | String | Перевод на русский |
| `transcript` | String | Фонетическая транскрипция |
| `code` | String | Код слова (для LinguaLeo?) |
| `owner` | String | ID владельца словаря |
| `link` | String | Ссылка на аудио произношение |
| `traini` | Boolean | Тренировано ли слово |
| `trainDate` | Date | Дата последней тренировки |
| `updateDate` | Date | Дата обновления |

---

## MongoDB Client API

### Инициализация

```python
from mongodb_client import get_vocabulary_client

vocab = get_vocabulary_client()
```

### Основные методы

#### 1. Проверка подключения

```python
if vocab.is_connected():
    print("Connected to MongoDB")
```

#### 2. Статистика словаря

```python
stats = vocab.get_word_count()
# Returns: {"total": 807, "trained": 450, "untrained": 357}
```

#### 3. Получить случайные слова

```python
# Любые 5 слов
words = vocab.get_random_words(count=5)

# Только тренированные слова
trained_words = vocab.get_random_words(count=5, trained=True)
```

#### 4. Получить не тренированные слова

```python
# Первые 10 нетренированных слов
untrained = vocab.get_untrained_words(count=10)
```

#### 5. Поиск слова

```python
word_data = vocab.search_word("epilraph")
if word_data:
    print(f"Translation: {word_data['translate']}")
```

#### 6. Отметить слово как тренированное

```python
success = vocab.mark_word_as_trained("epilraph")
```

#### 7. Форматировать слово для урока

```python
word_data = vocab.search_word("epilraph")
lesson_text = vocab.format_word_for_lesson(word_data)
# Returns: "Let's practice the word 'epilraph'. The pronunciation is [ˈepɪɡrɑːf]. In Russian, it means 'эпиграф'. Can you use 'epilraph' in a sentence?"
```

---

## Environment Variables

### Локальная разработка (`.env`):

```bash
MONGODB_URI=mongodb+srv://sergey0703:PASSWORD@cluster0.llssu.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=cluster0
MONGODB_COLLECTION=words
```

### Hugging Face Spaces (Secrets):

1. Откройте https://huggingface.co/spaces/YOUR_SPACE/settings
2. Tab "Variables and secrets"
3. Добавьте секреты:
   - `MONGODB_URI` = полный connection string
   - `MONGODB_DB` = `cluster0`
   - `MONGODB_COLLECTION` = `words`

---

## Тестирование

### Локально:

1. Установите зависимости:
```bash
pip install pymongo dnspython
```

2. Создайте `.env`:
```bash
cp .env.example .env
# Отредактируйте .env и добавьте MONGODB_URI с реальным паролем
```

3. Запустите тест:
```bash
python test_mongodb.py
```

**Ожидаемый вывод:**

```
============================================================
TESTING MONGODB VOCABULARY CLIENT
============================================================

✅ Connected: True

📊 VOCABULARY STATISTICS:
  Total words: 807
  Trained: 450
  Untrained: 357

🎲 RANDOM 5 WORDS:
  ✅ epilraph - эпиграф
  ❌ epilogue - эпилог
  ✅ epoch - эпоха
  ...

📖 UNTRAINED WORDS (first 3):
  📝 abandon - бросать
  📝 ability - способность
  ...

🔍 SEARCH WORD 'epilraph':
  Found: epilraph
  Translation: эпиграф
  Transcript: ˈepɪɡrɑːf
  Trained: True

📄 FORMATTED FOR LESSON:
  Let's practice the word 'epilraph'. The pronunciation is [ˈepɪɡrɑːf]. In Russian, it means 'эпиграф'. Can you use 'epilraph' in a sentence?

============================================================
✅ ALL TESTS COMPLETED
============================================================
```

---

## Интеграция с Agent

### Сценарий 1: Урок из словаря (вместо RSS)

```python
from mongodb_client import get_vocabulary_client

async def entrypoint(ctx: JobContext):
    vocab = get_vocabulary_client()

    if vocab.is_connected():
        # Получаем случайное нетренированное слово
        words = vocab.get_untrained_words(count=1)
        if words:
            word_data = words[0]
            lesson_text = vocab.format_word_for_lesson(word_data)
        else:
            # Fallback на тренированные слова
            words = vocab.get_random_words(count=1)
            word_data = words[0]
            lesson_text = vocab.format_word_for_lesson(word_data)
    else:
        # Fallback на RSS новости
        news = fetch_latest_news()
        lesson_text = format_lesson_from_news(news)

    # ... дальше инициализация агента с lesson_text
```

### Сценарий 2: Комбинированный урок (RSS + слова из словаря)

```python
async def entrypoint(ctx: JobContext):
    vocab = get_vocabulary_client()

    # Получаем новость
    news = fetch_latest_news()
    news_text = news['content']

    # Добавляем слова из словаря
    if vocab.is_connected():
        words = vocab.get_random_words(count=3)
        vocab_section = "\n\nToday's vocabulary:\n"
        for word_data in words:
            word = word_data['word']
            translate = word_data['translate']
            vocab_section += f"- {word} ({translate})\n"

        lesson_text = news_text + vocab_section
    else:
        lesson_text = news_text

    # ... дальше инициализация агента
```

### Сценарий 3: Интерактивная практика слов

После обсуждения новости agent может:

1. Спросить пользователя какое слово он хочет практиковать
2. Получить это слово из MongoDB
3. Практиковать использование слова в предложениях
4. Отметить слово как тренированное (`mark_word_as_trained`)

---

## Roadmap

### Phase 1 (Текущее): Read-only доступ ✅
- Получение случайных слов
- Поиск слов
- Статистика
- Форматирование для урока

### Phase 2: Интеграция с Agent
- [ ] Добавить опцию "урок из словаря" вместо RSS
- [ ] Комбинированные уроки (RSS + слова)
- [ ] Интерактивная практика слов

### Phase 3: Write operations
- [ ] Отмечать слова как тренированные
- [ ] Добавлять новые слова в словарь
- [ ] Обновлять статистику прогресса

### Phase 4: Advanced features
- [ ] Spaced repetition algorithm
- [ ] Персонализация по уровню сложности
- [ ] История использования слов
- [ ] Аналитика прогресса обучения

---

## Безопасность

⚠️ **ВАЖНО:**

1. **Никогда не коммитьте** connection string с паролем в Git
2. **Используйте Secrets** в HF Spaces для хранения `MONGODB_URI`
3. **MongoDB Network Access**: убедитесь что `0.0.0.0/0` разрешен для HF Spaces
4. **Database User**: используйте read-only user для production (опционально)

### MongoDB Atlas Network Access:

1. Откройте https://cloud.mongodb.com/
2. Network Access → IP Access List
3. Add IP Address → Allow Access from Anywhere (`0.0.0.0/0`)

---

## Troubleshooting

### Ошибка: "Authentication failed"
- Проверьте username и password в connection string
- Убедитесь что пароль URL-encoded (если содержит спецсимволы)

### Ошибка: "Connection timeout"
- Проверьте Network Access в MongoDB Atlas
- Добавьте `0.0.0.0/0` в IP Whitelist

### Ошибка: "Database/Collection not found"
- Проверьте название базы (`MONGODB_DB`)
- Проверьте название коллекции (`MONGODB_COLLECTION`)

### MongoDB Client returns empty results:
- Проверьте что коллекция `words` не пустая
- Проверьте query filters (например `traini: true/false`)

---

## Полезные ссылки

- MongoDB Atlas: https://cloud.mongodb.com/
- PyMongo Documentation: https://pymongo.readthedocs.io/
- Connection String Format: https://www.mongodb.com/docs/manual/reference/connection-string/
