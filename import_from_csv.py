import csv
from pymongo import MongoClient
from datetime import datetime

# MongoDB Configuration
URI = "mongodb+srv://appadmin:fDXtmowD2Z2PWfYx@cluster0.1lssu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "cluster0"
COLLECTION_NAME = "words"

def parse_csv_and_find_new_words(csv_file="ling.csv", dry_run=True):
    """
    Парсит CSV файл и находит слова, которых нет в MongoDB.
    
    Args:
        csv_file: путь к CSV файлу
        dry_run: если True, только показывает список новых слов без добавления
    """
    print(f"{'='*60}")
    print(f"IMPORT FROM CSV - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    print(f"Mode: {'DRY RUN (только показ списка)' if dry_run else 'IMPORT MODE'}")
    print(f"{'='*60}\n")
    
    try:
        # Подключение к MongoDB
        print("Подключение к MongoDB...")
        client = MongoClient(URI, serverSelectionTimeoutMS=10000)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # Получаем все слова из MongoDB
        print("Загрузка существующих слов из MongoDB...")
        existing_words = set()
        for doc in collection.find({}, {"word": 1}):
            existing_words.add(doc['word'].lower())
        
        print(f"Найдено {len(existing_words)} слов в MongoDB\n")
        
        # Парсим CSV файл
        print(f"Чтение файла {csv_file}...")
        new_words = []
        total_csv_words = 0
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            # CSV разделен точкой с запятой
            reader = csv.reader(f, delimiter=';')
            
            for row in reader:
                if len(row) < 2:
                    continue
                
                total_csv_words += 1
                
                # Первая колонка - слово, вторая - перевод
                word = row[0].strip().strip('"')
                translate = row[1].strip().strip('"')
                
                # Пропускаем пустые строки
                if not word or not translate:
                    continue
                
                # Проверяем, есть ли слово в MongoDB
                if word.lower() not in existing_words:
                    # Генерируем уникальный код для слова (timestamp + счетчик)
                    import time
                    unique_code = f"{int(time.time() * 1000)}_{total_csv_words}"
                    
                    # Создаем документ для добавления
                    new_word_doc = {
                        "word": word,
                        "translate": translate,
                        "stage": "new",
                        "code": unique_code,  # Добавляем уникальный код
                        # trainDate оставляем пустым (None)
                    }
                    
                    # Дополнительные поля из CSV (если есть)
                    if len(row) > 3 and row[3].strip().strip('"'):
                        new_word_doc["transcript"] = row[3].strip().strip('"')
                    
                    if len(row) > 4 and row[4].strip().strip('"'):
                        new_word_doc["example"] = row[4].strip().strip('"')
                    
                    if len(row) > 5 and row[5].strip().strip('"'):
                        new_word_doc["audio"] = row[5].strip().strip('"')
                    
                    new_words.append(new_word_doc)
        
        print(f"Всего слов в CSV: {total_csv_words}")
        print(f"Новых слов для добавления: {len(new_words)}\n")
        
        if not new_words:
            print("✓ Все слова из CSV уже есть в MongoDB!")
            return []
        
        # Показываем список новых слов
        print(f"{'='*60}")
        print(f"СПИСОК НОВЫХ СЛОВ ({len(new_words)} слов):")
        print(f"{'='*60}\n")
        
        for idx, word_doc in enumerate(new_words, 1):
            print(f"{idx}. {word_doc['word']} - {word_doc['translate']}")
            if 'transcription' in word_doc:
                print(f"   Транскрипция: {word_doc['transcription']}")
            if 'example' in word_doc:
                # Обрезаем длинные примеры
                example = word_doc['example']
                if len(example) > 80:
                    example = example[:77] + "..."
                print(f"   Пример: {example}")
        
        print(f"\n{'='*60}")
        print(f"Итого: {len(new_words)} новых слов")
        print(f"{'='*60}\n")
        
        if not dry_run:
            # Добавляем слова в MongoDB по одному (чтобы обработать ошибки дубликатов)
            print("Добавление слов в MongoDB...")
            inserted_count = 0
            skipped_count = 0
            
            for word_doc in new_words:
                try:
                    collection.insert_one(word_doc)
                    inserted_count += 1
                except Exception as e:
                    # Пропускаем слова с ошибками (например, дубликаты по индексу code)
                    skipped_count += 1
                    if "duplicate key" in str(e):
                        print(f"  Пропущено (дубликат): {word_doc['word']}")
                    else:
                        print(f"  Ошибка при добавлении '{word_doc['word']}': {e}")
            
            print(f"\n✓ Успешно добавлено {inserted_count} слов в MongoDB!")
            if skipped_count > 0:
                print(f"⚠ Пропущено {skipped_count} слов (дубликаты или ошибки)")
        else:
            print("⚠ DRY RUN MODE - Слова не были добавлены в базу.")
            print("Чтобы добавить слова, запустите скрипт с флагом --import:")
            print(f"  python import_from_csv.py --import\n")
        
        client.close()
        return new_words
        
    except FileNotFoundError:
        print(f"\n❌ Ошибка: Файл '{csv_file}' не найден!")
        print("Убедитесь, что файл находится в текущей директории.")
        return None
    except Exception as e:
        print(f"\n{'!'*60}")
        print("ОШИБКА")
        print(f"{'!'*60}")
        print(f"Детали: {e}")
        
        import traceback
        traceback.print_exc()
        return None

def main():
    import sys
    
    # Проверяем аргументы командной строки
    dry_run = True
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--import', '-i', '--add']:
            dry_run = False
            print("\n⚠ РЕЖИМ ИМПОРТА АКТИВИРОВАН")
            print("Новые слова будут добавлены в MongoDB.")
            
            # Запрашиваем подтверждение
            response = input("\nВы уверены, что хотите продолжить? (yes/no): ")
            if response.lower() not in ['yes', 'y', 'да']:
                print("Операция отменена.")
                return
    
    # Запускаем парсинг и поиск новых слов
    parse_csv_and_find_new_words(dry_run=dry_run)

if __name__ == "__main__":
    main()
