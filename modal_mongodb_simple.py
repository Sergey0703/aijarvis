"""
Simplified MongoDB API - Modal.com Deployment
Using web_endpoint instead of asgi_app to avoid encoding issues
"""
import os
import modal

# Modal Configuration
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "pymongo==4.10.1",
    "dnspython==2.7.0",
    "fastapi==0.115.0",
)

app = modal.App("vocab-api", image=image)

@app.function(
    secrets=[modal.Secret.from_name("mongodb-credentials")],
)
@modal.fastapi_endpoint(method="GET")
def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "vocabulary-api"}


@app.function(
    secrets=[modal.Secret.from_name("mongodb-credentials")],
)
@modal.fastapi_endpoint(method="GET")
def stats():
    """Get vocabulary statistics"""
    from pymongo import MongoClient

    MONGODB_URI = os.getenv("MONGODB_URI")
    MONGODB_DB = os.getenv("MONGODB_DB", "cluster0")
    MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "words")

    if not MONGODB_URI:
        return {"error": "MongoDB not configured"}, 503

    try:
        client = MongoClient(MONGODB_URI)
        db = client[MONGODB_DB]
        collection = db[MONGODB_COLLECTION]

        total = collection.count_documents({})
        trained = collection.count_documents({"traini": True})
        untrained = total - trained

        client.close()

        return {
            "total": total,
            "trained": trained,
            "untrained": untrained
        }
    except Exception as e:
        return {"error": str(e)}, 500


@app.function(
    secrets=[modal.Secret.from_name("mongodb-credentials")],
)
@modal.fastapi_endpoint(method="GET")
def random_words(count: int = 5, trained: bool = False):
    """Get random words from vocabulary"""
    from pymongo import MongoClient

    MONGODB_URI = os.getenv("MONGODB_URI")
    MONGODB_DB = os.getenv("MONGODB_DB", "cluster0")
    MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "words")

    if not MONGODB_URI:
        return {"error": "MongoDB not configured"}, 503

    try:
        client = MongoClient(MONGODB_URI)
        db = client[MONGODB_DB]
        collection = db[MONGODB_COLLECTION]

        query = {"traini": True} if trained else {}
        words = list(collection.aggregate([
            {"$match": query},
            {"$sample": {"size": count}}
        ]))

        # Convert ObjectId to string
        for word in words:
            if "_id" in word:
                word["_id"] = str(word["_id"])

        client.close()

        return {"words": words, "count": len(words)}
    except Exception as e:
        return {"error": str(e)}, 500
