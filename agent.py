import logging
import os
import re
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

# ========== ПОМОЩНИК ПАРСИНГА ==========
def parse_lesson_content(content: str):
    """
    Parses the lesson content into Vocabulary Focus and News Digest.
    """
    vocab_section = ""
    digest_section = content

    # Look for Vocabulary Focus
    vocab_match = re.search(r"Vocabulary Focus:(.*?)(?=---START_OF_DIGEST---|$)", content, re.DOTALL | re.IGNORECASE)
    if vocab_match:
        vocab_section = vocab_match.group(1).strip()

    # Look for Digest
    digest_match = re.search(r"---START_OF_DIGEST---(.*)", content, re.DOTALL)
    if digest_match:
        digest_section = digest_match.group(1).strip()
    
    return vocab_section, digest_section

# ========== СИСТЕМНЫЙ ПРОМПТ ==========
AGENT_INSTRUCTION = """
You are a friendly English Tutor named Aoede. Your goal is to help the user practice English.

ACTIVITIES:
1. Vocabulary Review: If 'Vocabulary Focus' is provided, you can help the user practice these words. 
   - Ask the user to translate a word or phrase.
   - Ask the user to pronounce a word. Since you are a voice agent, listen carefully to their pronunciation and provide feedback.
2. News Discussion: Discuss the news topics in the 'News Digest' section.

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
Hello! Greet the user naturally. 
If you see 'Vocabulary Focus' below, mention that you have some new words to review AND some news stories. Ask the user if they'd like to start with the vocabulary practice or jump straight into the news.
If there is NO 'Vocabulary Focus' but there are news stories, just list the news titles and ask which one to discuss.
If there's nothing, just say hello and ask how they're doing. 
Do not use bold text or headers.
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
    # 0. Clear logs at the start of every connection
    session_log.clear()
    logger.info("Starting English Tutor Agent - Session Log Reset")

    # 1. Define the report sending logic as a shutdown callback
    async def send_report():
        logger.info("Job is shutting down. Compiled report will be sent.")
        report = session_log.get_summary()
        await send_direct_email(
            subject=f"English Tutor Session Report: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            body=report
        )
        session_log.clear()
        logger.info("Session report sent successfully during shutdown.")

    # Register the callback with the JobContext (the official way)
    ctx.add_shutdown_callback(send_report)

    # 2. Setup the agent and fetch initial context
    lesson_text = await fetch_raw_news()
    
    vocab, digest = parse_lesson_content(lesson_text)
    
    context_parts = []
    if vocab:
        context_parts.append(f"VOCABULARY FOCUS (Review these with the user if they choose):\n{vocab}")
    
    if digest:
        context_parts.append(f"TODAY'S NEWS DIGEST:\n{digest}")
    elif news_text := lesson_text.strip():
        # Fallback if markers are missing
        context_parts.append(f"TODAY'S CONTENT:\n{news_text}")

    custom_instruction = AGENT_INSTRUCTION
    if context_parts:
        custom_instruction += "\n\n" + "\n\n".join(context_parts)
    
    session_instruction = SESSION_INSTRUCTION

    agent = EnglishTutorAgent()
    agent._instructions = custom_instruction
    
    session = AgentSession()
    setup_session_events(session)

    # 3. Connect and start the session
    await ctx.connect()
    logger.info("Agent connected to LiveKit room")

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            video_enabled=True,
        ),
    )

    try:
        await session.generate_reply(instructions=session_instruction)
        logger.info("Initial greeting delivered")
    except Exception as e:
        logger.warning(f"Initial greeting failed: {e}")

    # No loop needed here. The framework keeps the job alive while the room is connected.
    # The shutdown callback registered above will handle the email at the right time.

# ========== MAIN ==========
if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
    ))

