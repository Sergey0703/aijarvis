import logging
import os
import feedparser
import requests
from datetime import datetime
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RoomInputOptions,
    WorkerOptions,
    cli,
)
from livekit.plugins import google
from pymongo import MongoClient

# ========== ЛОГИРОВАНИЕ ==========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("english-tutor")

# ========== ВАЛИДАЦИЯ КЛЮЧЕЙ ==========
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    logger.error("GOOGLE_API_KEY not found")
    raise ValueError("GOOGLE_API_KEY is required")

logger.info("Google API Key found")

# ========== MONGODB CONFIGURATION ==========
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "cluster0")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "words")

def get_vocabulary_words(count: int = 5):
    """Get random untrained words from MongoDB vocabulary"""
    if not MONGODB_URI:
        logger.warning("MongoDB not configured, skipping vocabulary")
        return []

    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
        db = client[MONGODB_DB]
        collection = db[MONGODB_COLLECTION]

        # Get untrained words
        words = list(collection.find({"traini": False}).limit(count))

        # Convert ObjectId to string
        for word in words:
            if "_id" in word:
                word["_id"] = str(word["_id"])

        client.close()
        logger.info(f"Retrieved {len(words)} vocabulary words from MongoDB")
        return words
    except Exception as e:
        logger.error(f"Failed to get vocabulary words: {e}")
        return []

# ========== N8N WEBHOOK CONFIGURATION ==========
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/get-news")

# ========== RSS ИСТОЧНИКИ ==========
RSS_FEEDS = [
    "https://techcrunch.com/feed/",  # Technology news
    "http://feeds.bbci.co.uk/news/technology/rss.xml",  # BBC Tech
    "https://www.theverge.com/rss/index.xml",  # The Verge
]

# ========== ФУНКЦИЯ ПОЛУЧЕНИЯ НОВОСТЕЙ ==========
def fetch_latest_news(feed_url: str = None) -> dict:
    """
    Получает последнюю новость из RSS фида

    Returns:
        dict: {
            'title': str,
            'summary': str,
            'link': str,
            'published': str
        }
    """
    if feed_url is None:
        feed_url = RSS_FEEDS[0]  # По умолчанию TechCrunch

    try:
        logger.info(f"Fetching news from: {feed_url}")
        feed = feedparser.parse(feed_url)

        if not feed.entries:
            logger.warning("No entries found in RSS feed")
            return None

        # Берем первую (самую свежую) новость
        entry = feed.entries[0]

        news = {
            'title': entry.get('title', 'No title'),
            'summary': entry.get('summary', entry.get('description', 'No summary')),
            'link': entry.get('link', ''),
            'published': entry.get('published', 'Unknown date')
        }

        logger.info(f"Got news: {news['title'][:50]}...")
        return news

    except Exception as e:
        logger.error(f"Failed to fetch RSS: {e}")
        return None

def fetch_news_from_n8n() -> dict:
    """
    Получает случайную обработанную новость из N8N webhook

    Returns:
        dict: News object или None если ошибка
    """
    try:
        logger.info(f"Fetching news from N8N webhook: {N8N_WEBHOOK_URL}")
        response = requests.get(N8N_WEBHOOK_URL, timeout=10)

        if response.status_code == 200:
            news = response.json()

            # Проверка на ошибку от N8N
            if news.get('error') or news.get('fallback'):
                logger.warning(f"N8N returned error: {news.get('error', 'No news available')}")
                return None

            logger.info(f"Got news from N8N: {news.get('title', '')[:50]}...")
            return news
        else:
            logger.error(f"N8N webhook failed: HTTP {response.status_code}")
            return None

    except requests.exceptions.Timeout:
        logger.error("N8N webhook timeout")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to N8N webhook (N8N may not be ready yet)")
        return None
    except Exception as e:
        logger.error(f"Failed to fetch from N8N: {e}")
        return None

def format_lesson_from_news(news: dict) -> str:
    """
    Форматирует новость в текст урока
    """
    if not news:
        # Fallback на hardcoded текст
        return """
Welcome to your English practice.
Today's topic is Artificial Intelligence.
AI is rapidly transforming the modern workplace.
Instead of replacing jobs, experts suggest AI will augment human capabilities.
I am ready to discuss this with you. What do you think?
"""

    # Очищаем HTML теги из summary (feedparser может оставлять их)
    import re
    summary = re.sub(r'<[^>]+>', '', news['summary'])

    # Ограничиваем длину summary (макс 500 символов)
    if len(summary) > 500:
        summary = summary[:500] + "..."

    lesson_text = f"""
Welcome to your English practice.

Today's news: {news['title']}

{summary}

I am ready to discuss this article with you. What are your thoughts on this topic?
"""
    return lesson_text

# ========== HARDCODED ТЕКСТ УРОКА (FALLBACK) ==========
LESSON_TEXT = """
Welcome to your English practice.
Today's topic is Artificial Intelligence.
AI is rapidly transforming the modern workplace.
Instead of replacing jobs, experts suggest AI will augment human capabilities.
I am ready to discuss this with you. What do you think?
"""

# ========== СИСТЕМНЫЙ ПРОМПТ ==========
AGENT_INSTRUCTION = f"""
You are an English Tutor with video capability.
Your task is to read the lesson text below to the user clearly and slowly.

LESSON TEXT:
"{LESSON_TEXT.strip()}"

After reading, engage in a conversation about it.
Correct the user if they make grammar mistakes.
Keep responses conversational and natural for voice interaction.
Speak clearly and at a moderate pace suitable for English learners.

You can see and analyze video/images when users share their screen or camera.
If you see anything on video, acknowledge it and use it in conversation.
"""

SESSION_INSTRUCTION = """
Greet the user warmly.
Tell them you're ready to help them practice English.
Then read the lesson text about AI in the workplace.
After that, ask them what they think about the topic.
"""

# ========== GEMINI AGENT CLASS ==========
class EnglishTutorAgent(Agent):
    """Голосовой репетитор английского на базе Google Gemini Realtime Model"""

    def __init__(self) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
                model="gemini-live-2.5-flash-preview",
                voice="Aoede",
                temperature=0.7,
                api_key=google_api_key,
            ),
        )
        logger.info("EnglishTutorAgent initialized")

# ========== ОБРАБОТЧИКИ СОБЫТИЙ ==========
def setup_session_events(session: AgentSession):
    """Мониторинг работы агента"""

    @session.on("user_input_transcribed")
    def on_user_transcribed(event):
        transcript = getattr(event, 'transcript', '')
        is_final = getattr(event, 'is_final', False)
        if is_final:
            logger.info(f"👤 USER: {transcript}")

    @session.on("conversation_item_added")
    def on_conversation_item(event):
        item = getattr(event, 'item', None)
        if item:
            role = getattr(item, 'role', 'unknown')
            content = getattr(item, 'text_content', '')
            if content:
                logger.info(f"💬 {role.upper()}: {content[:100]}...")

    @session.on("error")
    def on_error(event):
        error = getattr(event, 'error', str(event))
        logger.error(f"ERROR: {error}")

    logger.info("Event handlers configured")

# ========== MAIN ENTRYPOINT ==========
async def entrypoint(ctx: JobContext):
    """Точка входа агента"""
    logger.info("Starting English Tutor Agent")

    # Пытаемся получить новость из N8N сначала
    news = fetch_news_from_n8n()

    # Если N8N не ответил, используем прямой RSS парсинг
    if not news:
        logger.info("Falling back to direct RSS fetch")
        news = fetch_latest_news()

    lesson_text = format_lesson_from_news(news)

    # Создаем кастомный промпт с новостью
    custom_instruction = f"""
You are an English Tutor with video capability.
Your task is to read the lesson text below to the user clearly and slowly.

LESSON TEXT:
"{lesson_text.strip()}"

After reading, engage in a conversation about it.
Correct the user if they make grammar mistakes.
Keep responses conversational and natural for voice interaction.
Speak clearly and at a moderate pace suitable for English learners.

You can see and analyze video/images when users share their screen or camera.
If you see anything on video, acknowledge it and use it in conversation.
"""

    custom_session_instruction = """
Greet the user warmly.
Tell them you're ready to help them practice English.
Then read today's news article to them.
After that, ask them what they think about the topic.
"""

    # Создаем агента с кастомными инструкциями
    agent = EnglishTutorAgent()
    agent._instructions = custom_instruction  # Обновляем инструкции для этой сессии

    session = AgentSession()
    setup_session_events(session)

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            video_enabled=True,
        ),
    )

    await ctx.connect()
    logger.info("Agent connected to LiveKit room")

    try:
        await session.generate_reply(instructions=custom_session_instruction)
        logger.info("Initial greeting delivered")
    except Exception as e:
        logger.warning(f"Greeting failed: {e}")

    logger.info("Agent ready")

# ========== MAIN ==========
if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        port=7860  # Hugging Face Spaces health check port
    ))
