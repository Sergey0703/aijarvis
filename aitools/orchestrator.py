"""
Orchestrator for AI Tools.
Collects and exports all available tools for the Gemini agent.
"""

from .news import get_today_news
from .email import send_user_email

# Unified list of tools to be passed to the Agent
AGENT_TOOLS = [
    get_today_news,
    send_user_email,
]

__all__ = [
    "AGENT_TOOLS",
]
