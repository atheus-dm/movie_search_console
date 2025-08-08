from pymongo import MongoClient
from dotenv import load_dotenv
import os
from typing import List, Dict, Any

# 🔐 Загрузка конфигурации из .env
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")

# 🗂 Подключение к Mongo
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
collection = db[MONGO_COLLECTION]


def get_top_keywords(limit: int = 5) -> List[Dict[str, Any]]:
    return list(collection.aggregate([
        {
            "$match": {
                "type": "keyword",
                "keyword": {"$nin": [None, "", "?", "—"]}
            }
        },
        {
            "$group": {
                "_id": "$keyword",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]))


def get_top_genres(limit: int = 5) -> List[Dict[str, Any]]:
    return list(collection.aggregate([
        {
            "$match": {
                "type": "genre_year",
                "genres": {"$nin": [None, "", "?", "—"]}
            }
        },
        {"$unwind": "$genres"},
        {
            "$group": {
                "_id": "$genres",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]))


def get_last_searches(limit: int = 5) -> List[Dict[str, Any]]:
    return list(collection.find(
        {},
        {"_id": 0, "type": 1, "keyword": 1, "genres": 1, "years": 1, "year": 1, "timestamp": 1}
    ).sort("timestamp", -1).limit(limit))