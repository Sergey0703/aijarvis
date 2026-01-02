import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

logger = logging.getLogger("mongo-tool")

class MongoHelper:
    def __init__(self):
        self.uri = os.getenv("MONGODB_URI")
        self.db_name = os.getenv("MONGODB_DATABASE") or "cluster0"
        self.collection_name = os.getenv("MONGODB_COLLECTION") or "words"
        self._client = None
        self._db = None

    async def connect(self):
        if not self._client:
            self._client = AsyncIOMotorClient(self.uri)
            self._db = self._client[self.db_name]
            logger.info(f"Connected to MongoDB: {self.db_name}")

    async def get_checked_words(self, limit: int = 15):
        """Fetches words approved for practice today."""
        await self.connect()
        collection = self._db[self.collection_name]
        
        # Cursor for words with stage 'checked'
        cursor = collection.find({"stage": "checked"}).limit(limit)
        words = await cursor.to_list(length=limit)
        
        # Format for the LLM
        return [{
            "word": w.get("word"),
            "translate": w.get("translate"),
            "_id": str(w.get("_id"))
        } for w in words]

    async def set_word_active(self, word_id: str):
        """Moves a word to 'active' practice stage after it's used in session."""
        await self.connect()
        from bson import ObjectId
        collection = self._db[self.collection_name]
        await collection.update_one(
            {"_id": ObjectId(word_id)},
            {"$set": {"stage": "active", "trainDate": datetime.now()}}
        )
        logger.info(f"Word {word_id} moved to 'active' stage")

# Singleton instance
mongo_helper = MongoHelper()
