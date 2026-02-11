from pymongo import MongoClient
import sys
import io

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HOST = "cluster0-shard-00-00.1lssu.mongodb.net:27017"
USER = "appadmin"
PASS = "fDXtmowD2Z2PWfYx"
URI = f"mongodb://{USER}:{PASS}@{HOST}/?ssl=true&authSource=admin&directConnection=true"

def check_date():
    try:
        client = MongoClient(URI, serverSelectionTimeoutMS=10000)
        db = client['cluster0']
        coll = db['words']

        # Точный подсчет слов с датой 2026-01-15
        count = coll.count_documents({"trainDate": {"$regex": "^2026-01-15"}})
        print(f"Слов с датой 2026-01-15**: {count}")

        # Покажем примеры
        print(f"\nПримеры слов (первые 10):")
        words = list(coll.find(
            {"trainDate": {"$regex": "^2026-01-15"}},
            {"word": 1, "trainDate": 1, "stage": 1, "_id": 1}
        ).limit(10))

        for i, w in enumerate(words, 1):
            print(f"  {i}. {w.get('word', '?')} - trainDate: {w.get('trainDate', '?')} - stage: {w.get('stage', '?')}")

        # Проверим также точный формат trainDate
        print(f"\n\nПроверка всех форматов trainDate для 2026-01-15:")

        formats = [
            "2026-01-15",
            {"$gte": "2026-01-15T00:00:00", "$lt": "2026-01-16T00:00:00"}
        ]

        for fmt in formats:
            if isinstance(fmt, str):
                count = coll.count_documents({"trainDate": fmt})
                print(f"  Точное совпадение '{fmt}': {count} слов")
            else:
                count = coll.count_documents({"trainDate": fmt})
                print(f"  Диапазон 2026-01-15 (дата-время): {count} слов")

        client.close()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_date()
