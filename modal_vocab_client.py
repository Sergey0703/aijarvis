"""
Modal MongoDB API Client
HTTP client for vocabulary operations via Modal.com API
"""
import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Modal API base URL - replace with your actual Modal deployment URL
# Format: https://{workspace}--mongodb-vocabulary-api-fastapi-app.modal.run
MODAL_API_URL = "https://sergey070373--mongodb-vocabulary-api-fastapi-app.modal.run"


class ModalVocabularyClient:
    """Client for vocabulary operations via Modal API"""

    def __init__(self, api_url: str = MODAL_API_URL):
        self.api_url = api_url
        self.timeout = 10

    def is_connected(self) -> bool:
        """Check if Modal API is available"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=self.timeout)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to connect to Modal API: {e}")
            return False

    def get_stats(self) -> Dict[str, int]:
        """Get vocabulary statistics"""
        try:
            response = requests.get(f"{self.api_url}/stats", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"total": 0, "trained": 0, "untrained": 0}

    def get_random_words(self, count: int = 5, trained: bool = False) -> List[Dict]:
        """Get random words from vocabulary"""
        try:
            params = {"count": count, "trained": trained}
            response = requests.get(
                f"{self.api_url}/words/random",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("words", [])
        except Exception as e:
            logger.error(f"Failed to get random words: {e}")
            return []

    def get_untrained_words(self, count: int = 10) -> List[Dict]:
        """Get untrained words"""
        try:
            params = {"count": count}
            response = requests.get(
                f"{self.api_url}/words/untrained",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("words", [])
        except Exception as e:
            logger.error(f"Failed to get untrained words: {e}")
            return []

    def search_word(self, word: str) -> Optional[Dict]:
        """Search for a specific word"""
        try:
            params = {"word": word}
            response = requests.get(
                f"{self.api_url}/words/search",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("word")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.info(f"Word '{word}' not found")
                return None
            logger.error(f"Failed to search word: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to search word: {e}")
            return None

    def mark_word_as_trained(self, word: str) -> bool:
        """Mark word as trained"""
        try:
            response = requests.post(
                f"{self.api_url}/words/mark-trained",
                params={"word": word},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("success", False)
        except Exception as e:
            logger.error(f"Failed to mark word as trained: {e}")
            return False

    def format_word_for_lesson(self, word_data: Dict) -> str:
        """Format word for lesson"""
        word = word_data.get("word", "")
        translate = word_data.get("translate", "")
        transcript = word_data.get("transcript", "")

        text = f"Let's practice the word '{word}'."

        if transcript:
            text += f" The pronunciation is [{transcript}]."

        if translate:
            text += f" In Russian, it means '{translate}'."

        text += f" Can you use '{word}' in a sentence?"

        return text


# Singleton instance
_vocab_client = None


def get_vocabulary_client() -> ModalVocabularyClient:
    """Get global instance of ModalVocabularyClient"""
    global _vocab_client
    if _vocab_client is None:
        _vocab_client = ModalVocabularyClient()
    return _vocab_client
