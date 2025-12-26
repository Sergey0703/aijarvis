import pymongo
import json
from bson import json_util

# Simplified SRV URI
SRV_URI = "mongodb+srv://appadmin:fDXtmowD2Z2PWfYx@cluster0.1lssu.mongodb.net/cluster0?retryWrites=true&w=majority"
COLLECTION_NAME = "words"

def inspect():
    try:
        print(f"Connecting via SRV: {SRV_URI}")
        client = pymongo.MongoClient(SRV_URI)
        db = client.get_database() # Uses the one from URI
        collection = db[COLLECTION_NAME]
        
        print(f"Connected. Counting documents in '{COLLECTION_NAME}'...")
        count = collection.count_documents({})
        print(f"Total documents: {count}")
        
        print("\n--- SAMPLE DOCUMENTS ---")
        samples = list(collection.find().limit(3))
        for doc in samples:
            print(json.dumps(doc, indent=2, default=json_util.default))
            print("-" * 20)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect()
