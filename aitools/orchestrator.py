"""
Orchestrator for AI Tools.
Collects and exports all available tools for the Gemini agent.
"""

from .news import get_today_news
from .email import send_user_email
from .mongo import mongo_helper
from livekit.agents import function_tool, RunContext

@function_tool()
async def get_approved_words(context: RunContext):
    """
    Returns the list of English words that the user approved for practice today.
    Use this to suggest topics or check if the user knows recent vocabulary.
    """
    return await mongo_helper.get_checked_words()

@function_tool()
async def mark_word_active(context: RunContext, word_id: str):
    """
    Call this when the user successfully uses a practice word in conversation.
    This moves the word to the 'active' usage stage in the database.
    """
    await mongo_helper.set_word_active(word_id)
    return f"Word {word_id} marked as active."

# Unified list of tools to be passed to the Agent
AGENT_TOOLS = [
    get_today_news,
    send_user_email,
    get_approved_words,
    mark_word_active,
]

__all__ = [
    "AGENT_TOOLS",
]
