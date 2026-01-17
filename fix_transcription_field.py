from pymongo import MongoClient

# MongoDB Configuration
URI = "mongodb+srv://appadmin:fDXtmowD2Z2PWfYx@cluster0.1lssu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "cluster0"
COLLECTION_NAME = "words"

def fix_transcription_field():
    print("Подключение к MongoDB...")
    client = MongoClient(URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    # 1. Update many: rename 'transcription' to 'transcript'
    print("Renaming 'transcription' field to 'transcript'...")
    result = collection.update_many(
        { "transcription": { "$exists": True } },
        { "$rename": { "transcription": "transcript" } }
    )
    
    print(f"Matched documents: {result.matched_count}")
    print(f"Modified documents: {result.modified_count}")
    
    if result.modified_count > 0:
        print("✓ Successfully renamed field in all documents.")
    else:
        print("No documents found with 'transcription' field.")

    client.close()

if __name__ == "__main__":
    fix_transcription_field()
