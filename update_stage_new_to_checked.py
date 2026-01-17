from pymongo import MongoClient

# MongoDB Configuration
URI = "mongodb+srv://appadmin:fDXtmowD2Z2PWfYx@cluster0.1lssu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "cluster0"
COLLECTION_NAME = "words"

def update_stage():
    print("Подключение к MongoDB...")
    client = MongoClient(URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    # Count documents to be updated
    filter_query = { "stage": "new" }
    count = collection.count_documents(filter_query)
    print(f"Found {count} documents with stage='new'.")
    
    if count > 0:
        print("Updating stage from 'new' to 'checked'...")
        result = collection.update_many(
            filter_query,
            { "$set": { "stage": "checked" } }
        )
        print(f"Modified documents: {result.modified_count}")
        print("✓ Update complete.")
    else:
        print("No documents to update.")

    client.close()

if __name__ == "__main__":
    update_stage()
