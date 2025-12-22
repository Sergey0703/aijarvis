import logging
import os
from dotenv import load_dotenv

load_dotenv()

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RoomInputOptions,
    WorkerOptions,
    cli,
)
from livekit.plugins import google

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

# ========== N8N WEBHOOK CONFIGURATION ==========
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

# ========== ФУНКЦИЯ ПОЛУЧЕНИЯ УРОКА ==========
async def fetch_lesson_from_n8n() -> str:
    """
    Получает готовый текст урока из n8n
    """
    if not N8N_WEBHOOK_URL:
        logger.warning("N8N_WEBHOOK_URL not configured, using fallback")
        return None

    import aiohttp
    try:
        logger.info(f"Fetching lesson from n8n: {N8N_WEBHOOK_URL}")
        async with aiohttp.ClientSession() as session:
            async with session.get(N8N_WEBHOOK_URL, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    # Предполагаем, что n8n отдает { "content": "..." } или { "text": "..." }
                    lesson = data.get('content') or data.get('text')
                    if lesson:
                        logger.info("Lesson fetched from n8n successfully")
                        return lesson
                
                logger.warning(f"n8n returned status {response.status}")
                return None
    except Exception as e:
        logger.error(f"Failed to fetch from n8n: {e}")
        return None

# ========== СИСТЕМНЫЙ ПРОМПТ ==========
AGENT_INSTRUCTION = """
You are an English Tutor with video capability.
Your task is to help the user practice English.
Correct the user if they make grammar mistakes.
Keep responses conversational and natural for voice interaction.
Speak clearly and at a moderate pace suitable for English learners.

You can see and analyze video/images when users share their screen or camera.
If you see anything on video, acknowledge it and use it in conversation.
"""

SESSION_INSTRUCTION = """
Greet the user warmly.
Tell them you're ready to help them practice English.
Ask them what they would like to talk about today.
"""

# ========== GEMINI AGENT CLASS ==========
class EnglishTutorAgent(Agent):
    """Голосовой репетитор английского на базе Google Gemini Realtime Model"""

    def __init__(self) -> None:
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
                model="gemini-2.5-flash-native-audio-preview-12-2025",
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

    # Пытаемся получить урок из n8n
    lesson_text = await fetch_lesson_from_n8n()

    # СИСТЕМНЫЙ ПРОМПТ (динамический, если есть новость)
    if lesson_text:
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
        session_instruction = """
Greet the user warmly.
Tell them you're ready to help them practice English.
Then read the topic you've prepared for them.
After that, ask them what they think about it.
"""
    else:
        custom_instruction = AGENT_INSTRUCTION
        session_instruction = SESSION_INSTRUCTION

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
        await session.generate_reply(instructions=session_instruction)
        logger.info("Initial greeting delivered")
    except Exception as e:
        logger.warning(f"Greeting failed: {e}")

    logger.info("Agent ready")

# ========== MAIN ==========
if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
    ))

