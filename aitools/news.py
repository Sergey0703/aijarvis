import logging
import os
import aiohttp
import re
from livekit.agents import function_tool, RunContext
from .logging_helper import session_log

logger = logging.getLogger("news-tool")

def get_webhook_url():
    """Returns the n8n news webhook URL from environment."""
    return os.getenv("N8N_NEWS_WEBHOOK_URL") or os.getenv("N8N_WEBHOOK_URL")

def summarize_text(text: str, sentences_count: int = 4) -> str:
    """Simple helper to extract the first few sentences from text."""
    if not text:
        return ""
    # Split by common sentence delimiters (., !, ?) followed by space or newline
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    summary = " ".join(sentences[:sentences_count])
    return summary

async def fetch_news_data() -> list:
    """Helper to fetch raw JSON data from n8n."""
    webhook_url = get_webhook_url()
    if not webhook_url:
        logger.warning("N8N_NEWS_WEBHOOK_URL not configured")
        return None

    try:
        logger.info(f"Fetching news from n8n: {webhook_url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(webhook_url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Received data from n8n: {data}")
                    
                    # Ensure we always return a list for consistent processing
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict):
                        # Special case: n8n Aggregate node often wraps results in a 'data' key
                        if 'data' in data and isinstance(data['data'], list):
                            return data['data']
                        return [data]
                    return []
                else:
                    msg = f"n8n returned status {response.status}"
                    logger.warning(msg)
                    session_log.add_log("WARNING", msg, {"url": webhook_url})
                    return None
    except Exception as e:
        msg = f"Failed to fetch news: {e}"
        logger.error(msg)
        session_log.add_log("ERROR", msg)
        return None

async def fetch_raw_news() -> str:
    """
    Fetches and formats news for the agent.
    Used both at startup and as a tool.
    """
    items = await fetch_news_data()
    if items is None:
        session_log.add_log("ERROR", "News items is None (Service Down)")
        return "News service is currently unavailable."
    
    session_log.add_log("INFO", f"Fetched {len(items)} news items from n8n")
    if not items:
        return "No news available at the moment."

    formatted_news = []
    for i, item in enumerate(items, 1):
        title = item.get('title', 'No Title')
        text = item.get('text', '')
        summary = summarize_text(text, 4)
        formatted_news.append(f"{i}. TITLE: {title}\n   SUMMARY: {summary}\n")

    return "\n".join(formatted_news)

@function_tool()
async def get_today_news(context: RunContext) -> str:
    """
    Fetch the latest news and topics for English practice.
    Use this tool if the user asks for news, what's new, or wants a topic to discuss.
    It returns a list of titles and short summaries.
    """
    logger.info("Dynamic news fetch triggered by agent")
    return await fetch_raw_news()
