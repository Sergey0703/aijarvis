from pymongo import MongoClient
from datetime import datetime
import sys
import io

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HOST = "cluster0-shard-00-00.1lssu.mongodb.net:27017"
USER = "appadmin"
PASS = "fDXtmowD2Z2PWfYx"
URI = f"mongodb://{USER}:{PASS}@{HOST}/?ssl=true&authSource=admin&directConnection=true"

def check_today():
    try:
        client = MongoClient(URI, serverSelectionTimeoutMS=10000)
        db = client['cluster0']
        coll = db['words']

        # Сегодня 2026-02-09
        start = datetime(2026, 2, 9, 0, 0, 0)
        end = datetime(2026, 2, 10, 0, 0, 0)

        count = coll.count_documents({
            "trainDate": {"$gte": start, "$lt": end}
        })

        print(f"Слов с датой 2026-02-09 (сегодня): {count}")

        # Группировка по stage
        pipeline = [
            {"$match": {"trainDate": {"$gte": start, "$lt": end}}},
            {"$group": {"_id": "$stage", "count": {"$sum": 1}}}
        ]

        stages = list(coll.aggregate(pipeline))
        print(f"\nРаспределение по stage:")
        for s in stages:
            print(f"  {s['_id']}: {s['count']} слов")

        # Примеры слов
        print(f"\nПримеры слов (первые 20):")
        words = list(coll.find(
            {"trainDate": {"$gte": start, "$lt": end}},
            {"word": 1, "trainDate": 1, "stage": 1}
        ).sort("trainDate", 1).limit(20))

        for i, w in enumerate(words, 1):
            print(f"  {i}. {w.get('word', '?'):20} - {w.get('trainDate')} - stage: {w.get('stage')}")

        client.close()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_today()
