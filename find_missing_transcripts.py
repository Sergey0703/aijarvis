from pymongo import MongoClient

# MongoDB Configuration
URI = "mongodb+srv://appadmin:fDXtmowD2Z2PWfYx@cluster0.1lssu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "cluster0"
COLLECTION_NAME = "words"

def find_missing_transcripts():
    print("Подключение к MongoDB...")
    try:
        client = MongoClient(URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # Query for missing or empty transcript
        # We check for:
        # 1. Field does not exist
        # 2. Field exists but is empty string
        # 3. Field exists but is null
        query = {
            "$or": [
                { "transcript": { "$exists": False } },
                { "transcript": "" },
                { "transcript": None }
            ]
        }
        
        count = collection.count_documents(query)
        print(f"Слов c отсутствующей транскрипцией: {count}")
        
        if count > 0:
            print("Примеры (первые 20):")
            cursor = collection.find(query).limit(20)
            for doc in cursor:
                print(f"Word: {doc.get('word')}, ID: {doc.get('_id')}")
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_missing_transcripts()
