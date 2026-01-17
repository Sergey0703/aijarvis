from pymongo import MongoClient

# MongoDB Configuration
URI = "mongodb+srv://appadmin:fDXtmowD2Z2PWfYx@cluster0.1lssu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "cluster0"
COLLECTION_NAME = "words"

def find_repeat_words():
    print("Подключение к MongoDB...")
    try:
        client = MongoClient(URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # Query for stage='repeat'
        filter_query = { "stage": "repeat" }
        
        # Get count
        count = collection.count_documents(filter_query)
        print(f"Всего слов со статусом 'repeat': {count}")
        print("-" * 30)
        
        if count > 0:
            # List all of them (or many)
            cursor = collection.find(filter_query)
            for i, doc in enumerate(cursor, 1):
                word = doc.get('word', 'N/A')
                trans = doc.get('translate', 'N/A')
                print(f"{i}. {word} - {trans}")
                
        else:
            print("Слов со статусом 'repeat' не найдено.")

        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_repeat_words()
