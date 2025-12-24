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
from aitools.orchestrator import AGENT_TOOLS
from aitools.news import fetch_raw_news

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

# ========== REMOVED LEGACY FETCH ==========
# fetch_lesson_from_n8n moved to aitools.news.fetch_raw_news

# ========== СИСТЕМНЫЙ ПРОМПТ ==========
AGENT_INSTRUCTION = """
You are a friendly English Tutor named Aoede. Your goal is to help the user practice English.

STRICT RULES:
1. NEVER USE BOLD TEXT. No asterisks ** allowed.
2. NEVER USE HEADERS or titles like "Thinking" or "Assessing".
3. NEVER talk about your own internal logic, design, or tools.
4. Just speak naturally, like a real person on a phone call.

If you have news topics, list the titles naturally. For example: "I found a few interesting stories for our lesson today. First, there is... Second... Which one sounds interesting?"
Keep summaries very short (3-4 sentences). Always ask the user a question after a summary.
If you do not have news, just start a friendly conversation about their day.
"""

SESSION_INSTRUCTION = """
Hello! Greet the user naturally. If you see news titles below, list them and ask which one to discuss. If there are no news items, just say hello and ask how they are. Do not use bold text or headers.
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
            tools=AGENT_TOOLS,
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

    # Dynamic instructions based on news availability
    lesson_text = await fetch_raw_news()
    
    if lesson_text:
        custom_instruction = f"{AGENT_INSTRUCTION}\n\nTODAY'S NEWS FOR THIS LESSON:\n{lesson_text.strip()}"
        session_instruction = SESSION_INSTRUCTION
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

