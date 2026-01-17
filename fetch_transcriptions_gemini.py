import os
import json
import re
import time
from dotenv import load_dotenv
from pymongo import MongoClient
import google.generativeai as genai
from google.api_core import exceptions

# Load env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('GOOGLE_API_KEY='):
                    api_key = line.strip().split('=')[1]
                    break
    except:
        pass

if not api_key:
    print("ERROR: GOOGLE_API_KEY not found.")
    exit(1)

genai.configure(api_key=api_key)
MODEL_NAME = 'gemini-2.5-flash'
model = genai.GenerativeModel(MODEL_NAME)

# MongoDB
URI = "mongodb+srv://appadmin:fDXtmowD2Z2PWfYx@cluster0.1lssu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "cluster0"
COLLECTION_NAME = "words"

def has_cyrillic(text):
    return bool(re.search('[а-яА-Я]', text))

def clean_json_string(s):
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```\w*\n", "", s)
        s = re.sub(r"\n```$", "", s)
    return s.strip()

def process_batch(collection, batch_words, retry_count=0):
    if not batch_words:
        return 0
    
    words_list_str = ", ".join([f'"{w["word"]}"' for w in batch_words])
    
    prompt = f"""
    You are a linguistic expert. I have a list of words. 
    Please provide the IPA transcription for each valid English word.
    
    Rules:
    1. Return ONLY a valid JSON object. No markdown, no explanations.
    2. The JSON keys should be the words from the list.
    3. The values should be the IPA transcription string.
    4. If a word is NOT a valid english word or is misspelled beyond recognition, do not include it in the JSON.
    5. If a word is a phrase, provide transcription for the phrase.
    
    Words: [{words_list_str}]
    """
    
    try:
        print(f"Requesting Gemini for {len(batch_words)} words...", end="", flush=True)
        response = model.generate_content(prompt)
        print(" Done.")
        text = clean_json_string(response.text)
        
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            print(f"  JSON Decode Error. Raw: {text[:50]}...")
            return 0
        
        updated_count = 0
        for doc in batch_words:
            word = doc['word']
            transcription = data.get(word)
            
            if transcription:
                collection.update_one(
                    { "_id": doc['_id'] },
                    { "$set": { "transcript": transcription } }
                )
                print(f"  ✓ {word}: {transcription}")
                updated_count += 1
            else:
                print(f"  - {word}: Not returned")
                
        return updated_count

    except exceptions.ResourceExhausted:
        wait_time = (2 ** retry_count) * 5 # 5, 10, 20...
        print(f"\n  Rate limit exceeded. Waiting {wait_time}s before retry ({retry_count+1}/3)...")
        if retry_count < 3:
            time.sleep(wait_time)
            return process_batch(collection, batch_words, retry_count + 1)
        else:
            print("  Max retries reached. Skipping batch.")
            return 0
    except Exception as e:
        print(f"\n  Error processing batch: {e}")
        return 0

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
    
    cursor = collection.find(query)
    all_docs = list(cursor)
    
    valid_docs = []
    skipped_cyrillic = 0
    for d in all_docs:
        w = d.get('word', '').strip()
        if w and not has_cyrillic(w):
             if len(w) < 50: 
                valid_docs.append({ "_id": d['_id'], "word": w })
        else:
            skipped_cyrillic += 1
            
    print(f"Found {len(all_docs)} total missing transcripts.")
    print(f"Skipped {skipped_cyrillic} (cyrillic/invalid).")
    print(f"Processing {len(valid_docs)} words with Gemini...")
    
    BATCH_SIZE = 5 # Reduced batch size
    total_updated = 0
    
    for i in range(0, len(valid_docs), BATCH_SIZE):
        batch = valid_docs[i : i + BATCH_SIZE]
        print(f"\nBatch {i//BATCH_SIZE + 1}/{len(valid_docs)//BATCH_SIZE + 1}:")
        updated = process_batch(collection, batch)
        total_updated += updated
        # Sleep nicely
        time.sleep(2)

    print("-" * 30)
    print(f"Total updated: {total_updated}")
    client.close()

if __name__ == "__main__":
    main()
