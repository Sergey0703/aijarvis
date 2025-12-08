"""
Скрипт для изучения структуры данных в MongoDB
"""
import os
from pymongo import MongoClient
from pprint import pprint

# MongoDB Connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://sergey0703:<password>@cluster0.llssu.mongodb.net/?retryWrites=true&w=majority")
MONGODB_DB = os.getenv("MONGODB_DB", "english_tutor")

def explore_mongodb():
    """Изучаем структуру данных в MongoDB"""

    print("🔍 Connecting to MongoDB...")

    # Подключаемся (нужно заменить <password> на реальный пароль)
    client = MongoClient(MONGODB_URI)

    print("📊 Available databases:")
    dbs = client.list_database_names()
    for db_name in dbs:
        print(f"  - {db_name}")

    # Работаем с базой english_tutor (или той которая есть у вас)
    db = client[MONGODB_DB]

    print(f"\n📁 Collections in '{MONGODB_DB}':")
    collections = db.list_collection_names()
    for coll_name in collections:
        count = db[coll_name].count_documents({})
        print(f"  - {coll_name}: {count} documents")

    # Смотрим примеры документов из каждой коллекции
    for coll_name in collections:
        print(f"\n📄 Sample document from '{coll_name}':")
        sample = db[coll_name].find_one()
        if sample:
            pprint(sample, indent=2)
        else:
            print("  (empty collection)")

    # Специально смотрим коллекцию со словами (предполагаем что она называется 'words' или 'vocabulary')
    if 'words' in collections:
        print("\n🔤 First 5 words from 'words' collection:")
        for word in db.words.find().limit(5):
            pprint(word, indent=2)

    if 'vocabulary' in collections:
        print("\n🔤 First 5 words from 'vocabulary' collection:")
        for word in db.vocabulary.find().limit(5):
            pprint(word, indent=2)

    client.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    explore_mongodb()
