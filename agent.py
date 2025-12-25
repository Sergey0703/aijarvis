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
from datetime import datetime
from livekit.plugins import google
from aitools.orchestrator import AGENT_TOOLS
from aitools.news import fetch_raw_news
from aitools.logging_helper import session_log
from aitools.email import send_direct_email

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

CRITICAL VOICE RULES (STRICT):
1. NEVER USE BOLD TEXT (**). 
2. NEVER USE HEADERS OR TITLES (e.g., # Header, ## Title).
3. NEVER USE LABELS like "Assessing the Input:", "Thinking:", or "Response:".
4. Speak only in plain text. No markdown. No special formatting.
5. Just speak naturally, like a real person on a phone call.

If you have news topics, list the titles naturally. Example: "I found a few stories. First, there's... Second... Which one sounds interesting?"
Keep summaries short (3-4 sentences). Always ask a question after a summary.
If you don't have news, just start a friendly conversation.
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
    # 0. Clear logs from any previous "zombie" session in the same worker process
    session_log.clear()
    logger.info("Starting English Tutor Agent - Session Log Reset")

    # Dynamic instructions based on news availability
    lesson_text = await fetch_raw_news()
    
    if lesson_text:
        custom_instruction = f"{AGENT_INSTRUCTION}\n\nTODAY'S NEWS FOR THIS LESSON:\n{lesson_text.strip()}"
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
        
        # Keep the agent alive while the room is connected AND there are participants
        # We exit as soon as the user leaves to send the report promptly
        while ctx.room.is_connected():
            remote_participants = [p for p in ctx.room.remote_participants.values()]
            if not remote_participants:
                logger.info("All participants left. Exiting session loop.")
                break
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.warning(f"Session encountered an error: {e}")
    finally:
        logger.info("Cleanly ending session. Sending session report...")
        report = session_log.get_summary()
        # Explicitly await the email send before the job process potentially dies
        await send_direct_email(
            subject=f"English Tutor Session Report: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            body=report
        )
        session_log.clear()
        logger.info("Session report sent and log cleared.")

# ========== MAIN ==========
if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
    ))

