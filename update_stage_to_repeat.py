from pymongo import MongoClient

# MongoDB Configuration
URI = "mongodb+srv://appadmin:fDXtmowD2Z2PWfYx@cluster0.1lssu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "cluster0"
COLLECTION_NAME = "words"

TARGET_WORDS = [
    "startle",
    "accustom",
    "awe",
    "strait",
    "plight",
    "sought",
    "embezzlement",
    "negligence",
    "flicker",
    "pasture"
]

def update_words_stage():
    print("Подключение к MongoDB...")
    try:
        client = MongoClient(URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        print(f"Updating stage to 'repeat' for {len(TARGET_WORDS)} words...")
        
        # Method 1: Update one by one to track individual success
        updated_count = 0
        for word in TARGET_WORDS:
            result = collection.update_one(
                { "word": word },
                { "$set": { "stage": "repeat" } }
            )
            if result.modified_count > 0:
                print(f"✓ Updated '{word}'")
                updated_count += 1
            elif result.matched_count > 0:
                print(f"- '{word}' already has stage='repeat' (or no change needed)")
            else:
                print(f"⚠ Word '{word}' not found in database")
                
        print("-" * 30)
        print(f"Total updated: {updated_count}/{len(TARGET_WORDS)}")

        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_words_stage()
