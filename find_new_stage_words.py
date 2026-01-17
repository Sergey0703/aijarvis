from pymongo import MongoClient

# MongoDB Configuration
URI = "mongodb+srv://appadmin:fDXtmowD2Z2PWfYx@cluster0.1lssu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "cluster0"
COLLECTION_NAME = "words"

def find_new_words():
    print("Подключение к MongoDB...")
    try:
        client = MongoClient(URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # Query for stage='new'
        filter_query = { "stage": "new" }
        
        # Get count first
        count = collection.count_documents(filter_query)
        print(f"Всего найдено слов со статусом 'new': {count}")
        print("-" * 30)
        
        if count > 0:
            # Find and print, limit to 100 just in case there are thousands to avoid spamming terminal
            cursor = collection.find(filter_query).limit(100)
            for doc in cursor:
                # Print word and maybe translation if available, or just the whole doc simplified
                word = doc.get('word', 'N/A')
                print(f"Word: {word}")
            
            if count > 100:
                print("-" * 30)
                print(f"... и еще {count - 100} слов.")
        else:
            print("Слов со статусом 'new' не найдено.")

        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_new_words()
