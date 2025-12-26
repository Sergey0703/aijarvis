import os
import json
from datetime import datetime
from pymongo import MongoClient
import traceback

# Configuration (from your previous messages)
URI = "mongodb+srv://appadmin:fDXtmowD2Z2PWfYx@cluster0.1lssu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "cluster0"
COLLECTION_NAME = "words"

def run_backup():
    print(f"--- MONGODB BACKUP START ({datetime.now().strftime('%H:%M:%S')}) ---")
    
    # 1. Prepare backup directory
    date_str = datetime.now().strftime("%Y%m%d")
    backup_file = f"words_backup_{date_str}.json"
    
    try:
        print(f"Connecting to MongoDB...")
        # We use a 10s timeout to not hang forever if DNS is broken
        client = MongoClient(URI, serverSelectionTimeoutMS=10000)
        
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        print(f"Reading collection '{COLLECTION_NAME}'...")
        count = collection.count_documents({})
        print(f"Found {count} documents. Starting export...")
        
        data = list(collection.find())
        
        # 2. Convert to JSON strings (handling ObjectId and Date)
        print(f"Saving to {backup_file}...")
        
        # Helper to handle MongoDB BSON types
        def json_serial(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if hasattr(obj, '__str__'):
                return str(obj)
            raise TypeError ("Type %s not serializable" % type(obj))

        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(data, f, default=json_serial, indent=2, ensure_ascii=False)
            
        print(f"\n[SUCCESS] Backup saved to {os.path.abspath(backup_file)}")
        print(f"Total words backed up: {len(data)}")

    except Exception as e:
        print("\n[ERROR] Backup failed!")
        print("-" * 30)
        # Check if it's a DNS issue
        if "getaddrinfo failed" in str(e) or "no such host" in str(e).lower():
            print("CRITICAL: DNS Resolution error. Your computer cannot find 'llssu.mongodb.net'.")
            print("POSSIBLE FIXES:")
            print("1. Check if you are using a VPN. Try turning it ON (or OFF).")
            print("2. Check for typos in the hostname (llssu).")
            print("3. Try changing Windows DNS to 8.8.8.8.")
        else:
            print(f"Details: {e}")
            traceback.print_exc()
        print("-" * 30)

if __name__ == "__main__":
    run_backup()
