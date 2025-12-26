import pymongo
import json
from bson import json_util

URI = "mongodb://appadmin:fDXtmowD2Z2PWfYx@cluster0-shard-00-00.1lssu.mongodb.net:27017,cluster0-shard-00-01.1lssu.mongodb.net:27017,cluster0-shard-00-02.1lssu.mongodb.net:27017/?ssl=true&replicaSet=atlas-6h6fu5-shard-0&authSource=admin&retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "cluster0"
COLLECTION_NAME = "words"

def inspect():
    try:
        client = pymongo.MongoClient(URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        print(f"Connecting to collection: {COLLECTION_NAME}")
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
