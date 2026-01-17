from pymongo import MongoClient

# MongoDB Configuration
URI = "mongodb+srv://appadmin:fDXtmowD2Z2PWfYx@cluster0.1lssu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "cluster0"
COLLECTION_NAME = "words"

def remove_weird_field():
    print("Подключение к MongoDB...")
    try:
        client = MongoClient(URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # Define the weird field key
        weird_key = "stage = new"
        
        # Check current count
        query = { weird_key: { "$exists": True } }
        count_before = collection.count_documents(query)
        print(f"Документов с полем '{weird_key}' перед удалением: {count_before}")
        
        if count_before > 0:
            print(f"Удаляю поле '{weird_key}' у {count_before} документов...")
            
            # Use $unset to remove the field
            # unset value can be anything, typically "" or 1
            result = collection.update_many(
                query,
                { "$unset": { weird_key: "" } }
            )
            
            print(f"Изменено документов: {result.modified_count}")
            
            # Verify
            count_after = collection.count_documents(query)
            print(f"Документов с полем '{weird_key}' после удаления: {count_after}")
            
            if count_after == 0:
                print("✓ Успешно очищено.")
            else:
                print("⚠ Внимание: не все поля были удалены.")
        else:
            print("Нет документов для исправления.")

        client.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    remove_weird_field()
