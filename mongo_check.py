from pymongo import MongoClient

HOST = "cluster0-shard-00-00.1lssu.mongodb.net:27017"
USER = "appadmin"
PASS = "fDXtmowD2Z2PWfYx"
# IMPORTANT: Use directConnection=True to bypass replica set issues if any
URI = f"mongodb://{USER}:{PASS}@{HOST}/?ssl=true&authSource=admin&directConnection=true"

def check(target_word="come"):
    try:
        client = MongoClient(URI, serverSelectionTimeoutMS=10000)
        db = client['cluster0']
        coll = db['words']
        word = coll.find_one({"word": target_word})
        if word:
            print(f"WORD FOUND: {word['word']}")
            print(f"STAGE: {word.get('stage')}")
            print(f"ID: {word['_id']}")
        else:
            print(f"WORD '{target_word}' NOT FOUND")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    import sys
    word_to_check = sys.argv[1] if len(sys.argv) > 1 else "come"
    check(word_to_check)
