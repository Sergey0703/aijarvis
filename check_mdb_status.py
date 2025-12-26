from pymongo import MongoClient

URI = "mongodb+srv://appadmin:fDXtmowD2Z2PWfYx@cluster0.1lssu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "cluster0"
COLLECTION_NAME = "words"

def check_status():
    try:
        client = MongoClient(URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        coll = db[COLLECTION_NAME]
        
        stats = list(coll.aggregate([
            {"$group": {"_id": "$stage", "count": {"$sum": 1}}}
        ]))
        
        print("--- MONGODB STAGE STATUS ---")
        for s in stats:
            stage_name = s['_id'] if s['_id'] else "None"
            print(f"Stage '{stage_name}': {s['count']} words")
            
        # Also show the last few 'checked' words
        checked_words = list(coll.find({"stage": "checked"}).sort("trainDate", -1).limit(5))
        if checked_words:
            print("\nRecent 'checked' words (ready for practice):")
            for w in checked_words:
                print(f" - {w['word']} ({w['translate']})")
        else:
            print("\nNo words in 'checked' stage yet.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_status()
