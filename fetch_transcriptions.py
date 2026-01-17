import requests
import time
import re
from pymongo import MongoClient

# MongoDB Configuration
URI = "mongodb+srv://appadmin:fDXtmowD2Z2PWfYx@cluster0.1lssu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "cluster0"
COLLECTION_NAME = "words"

API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{}"

def has_cyrillic(text):
    return bool(re.search('[а-яА-Я]', text))

def fetch_transcription(word):
    try:
        response = requests.get(API_URL.format(word))
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list):
                entry = data[0]
                # Try to find phonetic
                phonetic = entry.get('phonetic')
                if not phonetic and 'phonetics' in entry:
                    for p in entry['phonetics']:
                        if 'text' in p and p['text']:
                            phonetic = p['text']
                            break
                return phonetic
    except Exception as e:
        print(f"  Error fetching {word}: {e}")
    return None

def main():
    print("Подключение к MongoDB...")
    client = MongoClient(URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    query = {
        "$or": [
            { "transcript": { "$exists": False } },
            { "transcript": "" },
            { "transcript": None }
        ]
    }
    
    # Get all candidate documents
    cursor = collection.find(query)
    # Convert to list to avoid cursor timeout if processing takes long, 
    # though with 765 docs it should be fine. List is safer.
    docs = list(cursor)
    
    print(f"Found {len(docs)} words with missing transcription.")
    
    updated_count = 0
    skipped_cyrillic = 0
    not_found = 0
    
    for doc in docs:
        word = doc.get('word')
        if not word:
            continue
            
        word = word.strip()
        
        # Skip Cyrillic (Russian) words
        if has_cyrillic(word):
            skipped_cyrillic += 1
            print(f"Skipping Cyrillic word: {word}")
            continue
            
        print(f"Fetching transcription for '{word}'...", end="", flush=True)
        
        transcription = fetch_transcription(word)
        
        if transcription:
            print(f" FOUND: {transcription}")
            collection.update_one(
                { "_id": doc['_id'] },
                { "$set": { "transcript": transcription } }
            )
            updated_count += 1
        else:
            print(" NOT FOUND")
            not_found += 1
            
        # Be nice to the API
        time.sleep(0.5)
        
    print("-" * 30)
    print(f"Processing complete.")
    print(f"Updated: {updated_count}")
    print(f"Skipped (Cyrillic): {skipped_cyrillic}")
    print(f"Not found in API: {not_found}")
    
    client.close()

if __name__ == "__main__":
    main()
