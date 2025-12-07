import asyncio
import logging
import os
from datetime import datetime
from aiohttp import web
from livekit import agents
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RoomInputOptions,
    WorkerOptions,
)
from livekit.plugins import google

# ========== ЛОГИРОВАНИЕ (для Hugging Face Spaces) ==========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]  # HF Spaces захватывает stdout
)
logger = logging.getLogger("english-tutor")

# ========== ВАЛИДАЦИЯ КЛЮЧЕЙ ==========
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    logger.error("❌ GOOGLE_API_KEY не найден в переменных окружения")
    raise ValueError("GOOGLE_API_KEY обязателен для работы")

logger.info("✅ Google API Key найден")

# ========== HARDCODED ТЕКСТ УРОКА ==========
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

            # LLM внутри Agent (Agent-LLM архитектура)
            llm=google.beta.realtime.RealtimeModel(
                model="gemini-live-2.5-flash-preview",
                voice="Aoede",  # Женский голос
                temperature=0.7,
                api_key=google_api_key,
            ),
        )
        logger.info("✅ EnglishTutorAgent инициализирован (Gemini Realtime Model)")

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
        logger.error(f"❌ ERROR: {error}")

    logger.info("✅ Event handlers configured")

# ========== HTTP HEALTH ENDPOINT (для предотвращения засыпания HF Spaces) ==========
agent_start_time = datetime.now()

async def health_check(request):
    """Health check endpoint для мониторинга и keep-alive"""
    uptime = datetime.now() - agent_start_time
    return web.json_response({
        "status": "healthy",
        "service": "english-tutor-agent",
        "uptime_seconds": int(uptime.total_seconds()),
        "model": "gemini-live-2.5-flash-preview",
        "timestamp": datetime.now().isoformat()
    })

async def start_health_server():
    """Запуск HTTP сервера на порту 7860 (стандарт HF Spaces)"""
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)  # Root тоже отдает health

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 7860)
    await site.start()
    logger.info("✅ HTTP Health server started on port 7860")

# ========== MAIN ENTRYPOINT ==========
async def entrypoint(ctx: JobContext):
    """Точка входа агента"""

    logger.info("🚀 Starting English Tutor Agent (MVP - Hardcoded Text)")

    # Создаем пустую сессию (LLM живет в Agent)
    session = AgentSession()

    # Настраиваем события
    setup_session_events(session)

    # Запускаем сессию с видео поддержкой
    await session.start(
        room=ctx.room,
        agent=EnglishTutorAgent(),
        room_input_options=RoomInputOptions(
            video_enabled=True,  # Включаем видео
        ),
    )

    # Подключаемся к комнате
    await ctx.connect()

    logger.info("✅ Agent connected to LiveKit room")

    # Начальное приветствие и чтение текста урока
    try:
        await session.generate_reply(instructions=SESSION_INSTRUCTION)
        logger.info("✅ Initial greeting and lesson text delivered")
    except Exception as e:
        logger.warning(f"⚠️ Greeting failed: {e}")

    logger.info("🎙️ English Tutor Agent ready for conversation")
    logger.info(f"📖 Lesson Topic: AI in the workplace")

# ========== MAIN ==========
if __name__ == "__main__":
    # Запускаем HTTP health сервер в фоновом потоке
    async def run_with_health_server():
        # Стартуем health сервер
        await start_health_server()

        # Запускаем LiveKit CLI (блокирующий вызов)
        # Используем worker для запуска entrypoint при подключении
        from livekit.agents import Worker
        worker = Worker(WorkerOptions(entrypoint_fnc=entrypoint))
        await worker.run()

    asyncio.run(run_with_health_server())
