"""
MongoDB Client для работы со словарём пользователя
"""
import os
import logging
from typing import List, Dict, Optional
from pymongo import MongoClient
from datetime import datetime

logger = logging.getLogger(__name__)

# ========== MONGODB CONFIGURATION ==========
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "cluster0")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "words")


class VocabularyClient:
    """Клиент для работы со словарём в MongoDB"""

    def __init__(self):
        if not MONGODB_URI:
            logger.warning("⚠️ MONGODB_URI not set, vocabulary features disabled")
            self.client = None
            self.db = None
            self.collection = None
            return

        try:
            self.client = MongoClient(MONGODB_URI)
            self.db = self.client[MONGODB_DB]
            self.collection = self.db[MONGODB_COLLECTION]
            logger.info(f"✅ Connected to MongoDB: {MONGODB_DB}.{MONGODB_COLLECTION}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            self.client = None
            self.db = None
            self.collection = None

    def is_connected(self) -> bool:
        """Проверка подключения к MongoDB"""
        return self.collection is not None

    def get_random_words(self, count: int = 5, trained: bool = False) -> List[Dict]:
        """
        Получить случайные слова из словаря

        Args:
            count: Количество слов
            trained: Только тренированные слова (traini=True)

        Returns:
            List[Dict]: Список словарей со словами
        """
        if not self.is_connected():
            return []

        try:
            query = {"traini": True} if trained else {}
            words = list(self.collection.aggregate([
                {"$match": query},
                {"$sample": {"size": count}}
            ]))

            logger.info(f"📚 Retrieved {len(words)} words from MongoDB")
            return words

        except Exception as e:
            logger.error(f"❌ Failed to get random words: {e}")
            return []

    def get_untrained_words(self, count: int = 10) -> List[Dict]:
        """Получить не тренированные слова (traini=False)"""
        if not self.is_connected():
            return []

        try:
            words = list(self.collection.find(
                {"traini": False}
            ).limit(count))

            logger.info(f"📖 Retrieved {len(words)} untrained words")
            return words

        except Exception as e:
            logger.error(f"❌ Failed to get untrained words: {e}")
            return []

    def mark_word_as_trained(self, word: str) -> bool:
        """
        Отметить слово как тренированное

        Args:
            word: Английское слово

        Returns:
            bool: Успешно ли обновлено
        """
        if not self.is_connected():
            return False

        try:
            result = self.collection.update_one(
                {"word": word},
                {
                    "$set": {
                        "traini": True,
                        "trainDate": datetime.utcnow()
                    }
                }
            )

            if result.modified_count > 0:
                logger.info(f"✅ Marked word '{word}' as trained")
                return True
            else:
                logger.warning(f"⚠️ Word '{word}' not found or already trained")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to mark word as trained: {e}")
            return False

    def search_word(self, word: str) -> Optional[Dict]:
        """
        Найти слово в словаре

        Args:
            word: Английское слово

        Returns:
            Optional[Dict]: Словарь с данными слова или None
        """
        if not self.is_connected():
            return None

        try:
            word_data = self.collection.find_one({"word": word})

            if word_data:
                logger.info(f"🔍 Found word '{word}': {word_data.get('translate')}")
                return word_data
            else:
                logger.info(f"❌ Word '{word}' not found in vocabulary")
                return None

        except Exception as e:
            logger.error(f"❌ Failed to search word: {e}")
            return None

    def get_word_count(self) -> Dict[str, int]:
        """
        Получить статистику словаря

        Returns:
            Dict[str, int]: {"total": X, "trained": Y, "untrained": Z}
        """
        if not self.is_connected():
            return {"total": 0, "trained": 0, "untrained": 0}

        try:
            total = self.collection.count_documents({})
            trained = self.collection.count_documents({"traini": True})
            untrained = total - trained

            stats = {
                "total": total,
                "trained": trained,
                "untrained": untrained
            }

            logger.info(f"📊 Vocabulary stats: {stats}")
            return stats

        except Exception as e:
            logger.error(f"❌ Failed to get word count: {e}")
            return {"total": 0, "trained": 0, "untrained": 0}

    def format_word_for_lesson(self, word_data: Dict) -> str:
        """
        Форматировать слово для урока

        Args:
            word_data: Данные слова из MongoDB

        Returns:
            str: Отформатированный текст для урока
        """
        word = word_data.get("word", "")
        translate = word_data.get("translate", "")
        transcript = word_data.get("transcript", "")

        # Базовый формат
        text = f"Let's practice the word '{word}'."

        # Добавляем транскрипцию если есть
        if transcript:
            text += f" The pronunciation is [{transcript}]."

        # Добавляем перевод
        if translate:
            text += f" In Russian, it means '{translate}'."

        text += f" Can you use '{word}' in a sentence?"

        return text

    def close(self):
        """Закрыть соединение с MongoDB"""
        if self.client:
            self.client.close()
            logger.info("🔌 MongoDB connection closed")


# ========== SINGLETON INSTANCE ==========
_vocabulary_client = None


def get_vocabulary_client() -> VocabularyClient:
    """Получить глобальный instance VocabularyClient"""
    global _vocabulary_client
    if _vocabulary_client is None:
        _vocabulary_client = VocabularyClient()
    return _vocabulary_client
