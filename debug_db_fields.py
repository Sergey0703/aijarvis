from pymongo import MongoClient

# MongoDB Configuration
URI = "mongodb+srv://appadmin:fDXtmowD2Z2PWfYx@cluster0.1lssu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "cluster0"
COLLECTION_NAME = "words"

def investigate_issues():
    print("Подключение к MongoDB...")
    try:
        client = MongoClient(URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # 1. Check for field literally named "stage=new"
        print("Checking for documents with a KEY named 'stage=new'...")
        # To find if a key exists, we can use $exists. But key name needs to be exact.
        # "stage=new": { "$exists": True }
        weird_key_query = { "stage=new": { "$exists": True } }
        weird_key_count = collection.count_documents(weird_key_query)
        print(f"Found {weird_key_count} documents with KEY 'stage=new'.")
        
        if weird_key_count > 0:
            print("SAMPLE DOC with KEY 'stage=new':")
            print(collection.find_one(weird_key_query))

        # 2. Check for stage="stage=new"
        print("\nChecking for documents with stage='stage=new'...")
        weird_value_query = { "stage": "stage=new" }
        weird_value_count = collection.count_documents(weird_value_query)
        print(f"Found {weird_value_count} documents with stage='stage=new'.")
        
        # 3. Re-verify stage="new"
        print("\nChecking for documents with stage='new'...")
        normal_new_query = { "stage": "new" }
        normal_new_count = collection.count_documents(normal_new_query)
        print(f"Found {normal_new_count} documents with stage='new'.")
        
        if normal_new_count > 0:
            print("SAMPLE DOC with stage='new':")
            print(collection.find_one(normal_new_query))

        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    investigate_issues()
