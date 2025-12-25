import logging
from datetime import datetime

logger = logging.getLogger("logging-helper")

class SessionLogger:
    def __init__(self):
        self.logs = []
        self.start_time = datetime.now()

    def add_log(self, level: str, message: str, extra_data: dict = None):
        """Adds a log entry with timestamp."""
        entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "message": message,
            "data": extra_data or {}
        }
        self.logs.append(entry)
        logger.info(f"[{level}] {message}")

    def get_summary(self) -> str:
        """Formats all logs into a readable string."""
        if not self.logs:
            return "No activity recorded in this session."

        summary_lines = [
            f"--- SESSION REPORT ({self.start_time.strftime('%Y-%m-%d %H:%M:%S')}) ---",
            ""
        ]
        
        for entry in self.logs:
            line = f"[{entry['timestamp']}] [{entry['level']}] {entry['message']}"
            if entry['data']:
                line += f" | Data: {entry['data']}"
            summary_lines.append(line)
        
        return "\n".join(summary_lines)

    def clear(self):
        """Clears the session logs."""
        self.logs = []
        self.start_time = datetime.now()

# Global instance for the session
session_log = SessionLogger()
