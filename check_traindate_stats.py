from pymongo import MongoClient
from collections import defaultdict
from datetime import datetime
import sys
import io

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HOST = "cluster0-shard-00-00.1lssu.mongodb.net:27017"
USER = "appadmin"
PASS = "fDXtmowD2Z2PWfYx"
URI = f"mongodb://{USER}:{PASS}@{HOST}/?ssl=true&authSource=admin&directConnection=true"

def analyze_traindate_distribution():
    try:
        client = MongoClient(URI, serverSelectionTimeoutMS=10000)
        db = client['cluster0']
        coll = db['words']

        # Статистика
        total_words = coll.count_documents({})
        print(f"=== СТАТИСТИКА БАЗЫ ДАННЫХ ===\n")
        print(f"Всего слов в базе: {total_words}")

        # Считаем слова без trainDate
        null_traindate = coll.count_documents({"trainDate": None})
        empty_traindate = coll.count_documents({"trainDate": ""})
        missing_traindate = coll.count_documents({"trainDate": {"$exists": False}})

        print(f"Слова с trainDate = null: {null_traindate}")
        print(f"Слова с trainDate = '': {empty_traindate}")
        print(f"Слова без поля trainDate: {missing_traindate}")
        print(f"Слова БЕЗ даты (всего): {null_traindate + empty_traindate + missing_traindate}")

        # Группируем по датам
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

        print(f"\n=== РАСПРЕДЕЛЕНИЕ ПО ДАТАМ (всего дат: {len(date_groups)}) ===\n")

        # Группируем по годам
        by_year = defaultdict(int)
        by_month = defaultdict(int)

        for group in date_groups:
            date_str = group['_id']
            count = group['count']

            year = date_str[:4]
            year_month = date_str[:7]

            by_year[year] += count
            by_month[year_month] += count

        # Показываем по годам
        print("По годам:")
        for year in sorted(by_year.keys()):
            print(f"  {year}: {by_year[year]} слов")

        # Показываем по месяцам
        print("\nПо месяцам:")
        for ym in sorted(by_month.keys()):
            print(f"  {ym}: {by_month[ym]} слов")

        # Показываем первые 20 дат
        print("\n=== ПЕРВЫЕ 20 ДАТ (самые старые) ===")
        for i, group in enumerate(date_groups[:20]):
            print(f"  {i+1}. {group['_id']}: {group['count']} слов")

        # Показываем последние 20 дат
        print("\n=== ПОСЛЕДНИЕ 20 ДАТ (самые новые) ===")
        for i, group in enumerate(date_groups[-20:]):
            print(f"  {i+1}. {group['_id']}: {group['count']} слов")

        # Проверяем какие слова с датой 2026-01-15
        print("\n=== ПРИМЕРЫ СЛОВ С ДАТОЙ 2026-01-15 ===")
        sample_words = list(coll.find(
            {"trainDate": {"$regex": "^2026-01-15"}},
            {"word": 1, "trainDate": 1, "stage": 1}
        ).limit(10))

        for w in sample_words:
            print(f"  - {w.get('word', '?')} (stage: {w.get('stage', '?')}, trainDate: {w.get('trainDate', '?')})")

        print(f"\nВсего слов с датой 2026-01-15: {coll.count_documents({'trainDate': {'$regex': '^2026-01-15'}})}")

        # Проверяем есть ли слова с 2024 годом
        words_2024 = coll.count_documents({"trainDate": {"$regex": "^2024"}})
        print(f"\n=== СЛОВА ИЗ 2024 ГОДА ===")
        print(f"Всего слов с датой 2024-**: {words_2024}")

        if words_2024 > 0:
            print("\nПримеры слов из 2024:")
            sample_2024 = list(coll.find(
                {"trainDate": {"$regex": "^2024"}},
                {"word": 1, "trainDate": 1, "stage": 1}
            ).limit(10))
            for w in sample_2024:
                print(f"  - {w.get('word', '?')} (stage: {w.get('stage', '?')}, trainDate: {w.get('trainDate', '?')})")

        client.close()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_traindate_distribution()
