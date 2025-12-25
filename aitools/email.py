import logging
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from livekit.agents import function_tool, RunContext
from typing import Optional

logger = logging.getLogger("email-tool")

def get_email_config():
    """Returns email configuration from environment variables."""
    return {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "user": os.getenv("GMAIL_USER"),
        "password": os.getenv("GMAIL_APP_PASSWORD"),
        "admin_email": os.getenv("ADMIN_EMAIL")
    }

async def send_direct_email(subject: str, body: str, to_email: Optional[str] = None):
    """Internal function to send email without a tool context."""
    config = get_email_config()
    if not config["user"] or not config["password"]:
        logger.warning("Email credentials not configured. Skipping email.")
        return False

    recipient = to_email or config["admin_email"]
    if not recipient:
        logger.warning("No recipient email provided and ADMIN_EMAIL not set.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = config["user"]
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
        server.starttls()
        server.login(config["user"], config["password"])
        server.sendmail(config["user"], recipient, msg.as_string())
        server.quit()
        logger.info(f"Email sent successfully to {recipient}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

@function_tool()
async def send_user_email(
    context: RunContext,
    subject: str,
    message: str
) -> str:
    """
    Send an email message to the user or designated recipient.
    Use this when the user asks you to email them something (like lesson notes or lists).
    """
    to_email = os.getenv("ADMIN_EMAIL") # Default to admin for now
    if not to_email:
        return "I'm sorry, I don't have an email address configured to send to."

    success = await send_direct_email(subject, message, to_email)
    if success:
        return f"Email sent successfully to {to_email}."
    else:
        return "I encountered an error while trying to send the email."
