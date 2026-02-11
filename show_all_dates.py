from pymongo import MongoClient
import sys
import io

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HOST = "cluster0-shard-00-00.1lssu.mongodb.net:27017"
USER = "appadmin"
PASS = "fDXtmowD2Z2PWfYx"
URI = f"mongodb://{USER}:{PASS}@{HOST}/?ssl=true&authSource=admin&directConnection=true"

def show_all_dates():
    try:
        client = MongoClient(URI, serverSelectionTimeoutMS=10000)
        db = client['cluster0']
        coll = db['words']

        # Группировка по датам
        pipeline = [
            {"$match": {"trainDate": {"$ne": None, "$ne": "", "$exists": True}}},
            {"$addFields": {
                "trainDateParsed": {
                    "$cond": {
                        "if": {"$eq": [{"$type": "$trainDate"}, "date"]},
                        "then": "$trainDate",
                        "else": {"$toDate": "$trainDate"}
                    }
                }
            }},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$trainDateParsed"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}  # От старых к новым
        ]

        date_groups = list(coll.aggregate(pipeline))

        print(f"=== ВСЕ ДАТЫ И КОЛИЧЕСТВО СЛОВ ===\n")
        print(f"Всего дат: {len(date_groups)}\n")

        total_words = 0
        for i, group in enumerate(date_groups, 1):
            date_str = group['_id']
            count = group['count']
            total_words += count
            print(f"{i:2}. {date_str}: {count:5} слов")

        print(f"\n{'='*40}")
        print(f"ИТОГО: {total_words} слов")

        client.close()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    show_all_dates()
