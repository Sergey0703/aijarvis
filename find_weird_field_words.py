from pymongo import MongoClient

# MongoDB Configuration
URI = "mongodb+srv://appadmin:fDXtmowD2Z2PWfYx@cluster0.1lssu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "cluster0"
COLLECTION_NAME = "words"

def find_words_with_weird_field():
    print("Подключение к MongoDB...")
    try:
        client = MongoClient(URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # Check for field literally named "stage = new" (with spaces)
        print("Checking for documents with key 'stage = new' (with spaces)...")
        query = { "stage = new": { "$exists": True } }
        count = collection.count_documents(query)
        print(f"Found {count} documents with key 'stage = new'.")
        
        if count > 0:
            print("Listing first 20 such words:")
            cursor = collection.find(query).limit(20)
            for doc in cursor:
                # Print word and the value of that weird field
                word = doc.get('word', 'N/A')
                weird_val = doc.get('stage = new', "MISSING")
                print(f"Word: {word}, 'stage = new': {weird_val}")
        
        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_words_with_weird_field()
