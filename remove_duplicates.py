import os
import sys
from pymongo import MongoClient
from datetime import datetime
from collections import defaultdict

# Configuration - Using replica set URI for write operations
URI = "mongodb+srv://appadmin:fDXtmowD2Z2PWfYx@cluster0.1lssu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

DB_NAME = "cluster0"
COLLECTION_NAME = "words"

def find_duplicates(dry_run=True):
    """
    Find duplicate words in the MongoDB collection.
    
    Args:
        dry_run: If True, only report duplicates without removing them
    
    Returns:
        Dictionary with duplicate words and their document IDs
    """
    print(f"{'='*60}")
    print(f"DUPLICATE DETECTION SCRIPT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'DELETION MODE'}")
    print(f"{'='*60}\n")
    
    try:
        print("Connecting to MongoDB...")
        client = MongoClient(URI, serverSelectionTimeoutMS=10000)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        print(f"Connected to database: {DB_NAME}")
        print(f"Collection: {COLLECTION_NAME}")
        
        # Get total count
        total_count = collection.count_documents({})
        print(f"Total documents in collection: {total_count}\n")
        
        # Find duplicates using aggregation
        print("Searching for duplicates...")
        pipeline = [
            {
                "$group": {
                    "_id": "$word",
                    "count": {"$sum": 1},
                    "ids": {"$push": "$_id"},
                    "docs": {"$push": "$$ROOT"}
                }
            },
            {
                "$match": {
                    "count": {"$gt": 1}
                }
            },
            {
                "$sort": {"count": -1}
            }
        ]
        
        duplicates = list(collection.aggregate(pipeline))
        
        if not duplicates:
            print("\n✓ No duplicates found! Database is clean.")
            return {}
        
        # Display duplicates
        print(f"\n{'!'*60}")
        print(f"FOUND {len(duplicates)} DUPLICATE WORDS")
        print(f"{'!'*60}\n")
        
        duplicate_dict = {}
        total_duplicates = 0
        
        for dup in duplicates:
            word = dup['_id']
            count = dup['count']
            docs = dup['docs']
            
            duplicate_dict[word] = {
                'count': count,
                'documents': docs
            }
            
            total_duplicates += (count - 1)  # -1 because we keep one copy
            
            print(f"Word: '{word}' - Found {count} copies")
            for idx, doc in enumerate(docs):
                stage = doc.get('stage', 'N/A')
                doc_id = doc['_id']
                translate = doc.get('translate', 'N/A')
                train_date = doc.get('trainDate', 'N/A')
                
                marker = "  [KEEP]" if idx == 0 else "  [DELETE]"
                print(f"  {marker} ID: {doc_id} | Stage: {stage} | Translation: {translate} | TrainDate: {train_date}")
            print()
        
        print(f"{'='*60}")
        print(f"Summary:")
        print(f"  - Unique duplicate words: {len(duplicates)}")
        print(f"  - Total duplicate documents to remove: {total_duplicates}")
        print(f"  - Documents that will remain: {len(duplicates)}")
        print(f"{'='*60}\n")
        
        if not dry_run:
            # Delete duplicates (keep the first occurrence)
            print("Starting deletion process...")
            deleted_count = 0
            
            for word, data in duplicate_dict.items():
                docs = data['documents']
                # Keep the first document, delete the rest
                ids_to_delete = [doc['_id'] for doc in docs[1:]]
                
                if ids_to_delete:
                    result = collection.delete_many({"_id": {"$in": ids_to_delete}})
                    deleted_count += result.deleted_count
                    print(f"  Deleted {result.deleted_count} duplicate(s) of '{word}'")
            
            print(f"\n{'='*60}")
            print(f"DELETION COMPLETE")
            print(f"Total documents deleted: {deleted_count}")
            print(f"{'='*60}\n")
            
            # Verify
            new_count = collection.count_documents({})
            print(f"Documents before: {total_count}")
            print(f"Documents after: {new_count}")
            print(f"Difference: {total_count - new_count}")
        else:
            print("⚠ DRY RUN MODE - No changes were made to the database.")
            print("To actually remove duplicates, run with --delete flag:")
            print(f"  python {os.path.basename(__file__)} --delete\n")
        
        client.close()
        return duplicate_dict
        
    except Exception as e:
        print(f"\n{'!'*60}")
        print("ERROR OCCURRED")
        print(f"{'!'*60}")
        print(f"Details: {e}")
        
        if "getaddrinfo failed" in str(e) or "no such host" in str(e).lower():
            print("\nCRITICAL: DNS Resolution error.")
            print("POSSIBLE FIXES:")
            print("1. Check if you are using a VPN. Try turning it ON (or OFF).")
            print("2. Check for typos in the hostname.")
            print("3. Try changing Windows DNS to 8.8.8.8.")
        
        import traceback
        traceback.print_exc()
        return None

def main():
    # Check command line arguments
    dry_run = True
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--delete', '-d', '--remove']:
            dry_run = False
            print("\n⚠ WARNING: DELETION MODE ACTIVATED")
            print("This will permanently remove duplicate words from the database.")
            
            # Ask for confirmation
            response = input("\nAre you sure you want to continue? (yes/no): ")
            if response.lower() not in ['yes', 'y', 'да']:
                print("Operation cancelled.")
                return
            
            # Remind about backup
            print("\n⚠ IMPORTANT: Have you created a backup?")
            response = input("Type 'yes' to confirm you have a backup: ")
            if response.lower() not in ['yes', 'y', 'да']:
                print("\nPlease create a backup first using:")
                print("  python backup_db.py")
                print("\nOperation cancelled.")
                return
    
    # Run the duplicate detection/removal
    find_duplicates(dry_run=dry_run)

if __name__ == "__main__":
    main()
