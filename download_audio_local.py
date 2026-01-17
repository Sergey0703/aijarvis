import os
import re
import requests
from pymongo import MongoClient
from urllib.parse import urlparse

# MongoDB Configuration
URI = "mongodb+srv://appadmin:fDXtmowD2Z2PWfYx@cluster0.1lssu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "cluster0"
COLLECTION_NAME = "words"

# Local Directory Config
AUDIO_DIR = "downloaded_audio"

def extract_url(sound_field):
    """Extracts URL from [sound:https://...] format."""
    if not sound_field or not sound_field.startswith("[sound:"):
        return None
    return sound_field[7:-1]

def sanitize_filename(filename):
    """Removes invalid characters for filenames."""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def main():
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)
        print(f"Created directory: {AUDIO_DIR}")

    print("Connecting to MongoDB...")
    client = MongoClient(URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # Find documents with sound field
    query = {"sound": {"$exists": True, "$ne": ""}}
    docs = list(collection.find(query))
    print(f"Found {len(docs)} documents with sound field.")

    downloaded = 0
    skipped = 0
    errors = 0

    for doc in docs:
        word = doc.get('word')
        sound_field = doc.get('sound')
        
        if not word or not sound_field:
            continue

        url = extract_url(sound_field)
        if not url:
            print(f"  - Invalid sound format for word '{word}': {sound_field}")
            skipped += 1
            continue

        safe_word = sanitize_filename(word)
        file_path = os.path.join(AUDIO_DIR, f"{safe_word}.mp3")

        # Check if file already exists
        if os.path.exists(file_path):
            # print(f"  - File already exists for '{word}', skipping.")
            skipped += 1
            continue

        try:
            # print(f"  Downloading sound for '{word}'...")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                downloaded += 1
                if downloaded % 50 == 0:
                    print(f"Progress: {downloaded} files downloaded...")
            else:
                print(f"  - Failed to download '{word}': Status {response.status_code}")
                errors += 1
        except Exception as e:
            print(f"  - Error downloading '{word}': {e}")
            errors += 1

    print("-" * 30)
    print(f"Download complete.")
    print(f"Downloaded: {downloaded}")
    print(f"Skipped: {skipped}")
    print(f"Errors: {errors}")
    print(f"Files are in: {os.path.abspath(AUDIO_DIR)}")

if __name__ == "__main__":
    main()
