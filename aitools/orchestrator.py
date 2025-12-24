"""
Orchestrator for AI Tools.
Collects and exports all available tools for the Gemini agent.
"""

from .news import get_today_news

# Unified list of tools to be passed to the Agent
AGENT_TOOLS = [
    get_today_news,
]

__all__ = [
    "AGENT_TOOLS",
]
