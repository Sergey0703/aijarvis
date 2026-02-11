from pymongo import MongoClient
import sys
import io

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HOST = "cluster0-shard-00-00.1lssu.mongodb.net:27017"
USER = "appadmin"
PASS = "fDXtmowD2Z2PWfYx"
URI = f"mongodb://{USER}:{PASS}@{HOST}/?ssl=true&authSource=admin&directConnection=true"

def check_format():
    try:
        client = MongoClient(URI, serverSelectionTimeoutMS=10000)
        db = client['cluster0']
        coll = db['words']

        print("Проверка формата trainDate в базе данных:\n")

        # Берем первые 20 слов и смотрим формат trainDate
        words = list(coll.find({}, {"word": 1, "trainDate": 1}).limit(20))

        for i, w in enumerate(words, 1):
            td = w.get('trainDate')
            td_type = type(td).__name__
            print(f"{i}. {w.get('word', '?')[:15]:15} - trainDate: {td} (type: {td_type})")

        # Агрегация для группировки по дате
        print("\n\nАгрегация MongoDB (первые 5 групп):")
        pipeline = [
            {"$match": {"trainDate": {"$ne": None}}},
            {"$limit": 1000},
            {"$addFields": {
                "trainDateStr": {
                    "$cond": {
                        "if": {"$eq": [{"$type": "$trainDate"}, "date"]},
                        "then": {"$dateToString": {"format": "%Y-%m-%d", "date": "$trainDate"}},
                        "else": "$trainDate"
                    }
                }
            }},
            {"$group": {
                "_id": "$trainDateStr",
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}},
            {"$limit": 5}
        ]

        groups = list(coll.aggregate(pipeline))
        for g in groups:
            print(f"  {g['_id']}: {g['count']} слов")

        # Проверим точный тип поля trainDate
        print("\n\nПроверка типов trainDate:")
        type_check = list(coll.aggregate([
            {"$project": {
                "word": 1,
                "trainDate": 1,
                "trainDateType": {"$type": "$trainDate"}
            }},
            {"$limit": 10}
        ]))

        for w in type_check:
            print(f"  {w.get('word', '?')[:15]:15} - type: {w.get('trainDateType')} - value: {w.get('trainDate')}")

        client.close()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_format()
