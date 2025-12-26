import os
from pymongo import MongoClient
from datetime import datetime

# Configuration
URI = "mongodb+srv://appadmin:fDXtmowD2Z2PWfYx@cluster0.1lssu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "cluster0"
COLLECTION_NAME = "words"

def migrate():
    print(f"--- DATABASE MIGRATION START ---")
    
    try:
        client = MongoClient(URI, serverSelectionTimeoutMS=10000)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # 1. Initialize 'stage' field for all documents that don't have it
        print("Setting 'stage: new' for all words...")
        result = collection.update_many(
            {"stage": {"$exists": False}},
            {"$set": {"stage": "new"}}
        )
        print(f"Updated {result.modified_count} documents.")
        
        # 2. Summary
        total = collection.count_documents({})
        stages = collection.aggregate([
            {"$group": {"_id": "$stage", "count": {"$sum": 1}}}
        ])
        
        print(f"\nMigration Summary (Total: {total}):")
        for s in stages:
            print(f" - Stage '{s['_id']}': {s['count']} words")

        print("\n[SUCCESS] Migration completed.")

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")

if __name__ == "__main__":
    migrate()
