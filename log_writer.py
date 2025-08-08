from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import logging
from functools import wraps
from typing import Callable, Any, List

"""
Логирование поисковых запросов.

Примечание:
    Ниже представлены функции `log_keyword_search`, `log_genre_year_search`, `log_genre_exact_year_search`,
    которые были разработаны до внедрения универсального декоратора `@log_search`.

    Они не используются в текущей версии проекта, но оставлены:
        - как альтернатива для явного логирования без декораторов;
        - для возможного использования в тестах, отладке или при отказе от декораторов;
        - как часть истории развития логики логирования.

    При необходимости могут быть удалены или перенесены в архивный модуль.
"""



# 🛠 Настройка логирования в файл
logging.basicConfig(
    filename="log.txt",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)

# 🔐 Загрузка конфигурации из .env
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")

# 📡 Подключение к MongoDB
client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
collection = db[MONGO_COLLECTION]


def log_search(log_type: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if kwargs.get("logged", False):
                return func(*args, **kwargs)

            now = datetime.utcnow()

            if log_type == "keyword":
                keyword = args[0].lower().strip()
                if not keyword:
                    return func(*args, **kwargs)

                recent = collection.find_one({
                    "type": "keyword",
                    "keyword": keyword,
                    "timestamp": {"$gte": now - timedelta(seconds=5)}
                })
                if not recent:
                    collection.insert_one({
                        "type": "keyword",
                        "keyword": keyword,
                        "timestamp": now
                    })
                    logging.info(f"Лог сохранён: keyword → '{keyword}'")

            elif log_type == "genre_year":
                genres: List[str] = args[0]
                year_from = args[1]
                year_to = args[2]

                genres_clean = [g.strip() for g in genres if g and g.strip()]
                if not genres_clean:
                    return func(*args, **kwargs)

                year_range = f"{year_from}–{year_to}"

                recent = collection.find_one({
                    "type": "genre_year",
                    "genres": sorted(genres_clean),
                    "years": year_range,
                    "timestamp": {"$gte": now - timedelta(seconds=5)}
                })
                if not recent:
                    collection.insert_one({
                        "type": "genre_year",
                        "genres": sorted(genres_clean),
                        "years": year_range,
                        "timestamp": now
                    })
                    logging.info(f"Лог сохранён: genres → {genres_clean} | years → {year_range}")

            elif log_type == "genre_exact_year":
                genres: List[str] = args[0]
                raw_year = args[1]

                genres_clean = [g.strip() for g in genres if g and g.strip()]
                try:
                    year = int(raw_year)
                except (ValueError, TypeError):
                    year = None

                if not genres_clean or year is None or year < 1990:
                    return func(*args, **kwargs)

                recent = collection.find_one({
                    "type": "genre_exact_year",
                    "genres": sorted(genres_clean),
                    "year": year,
                    "timestamp": {"$gte": now - timedelta(seconds=5)}
                })
                if not recent:
                    collection.insert_one({
                        "type": "genre_exact_year",
                        "genres": sorted(genres_clean),
                        "year": year,
                        "timestamp": now
                    })
                    logging.info(f"Лог сохранён: genres → {genres_clean} | year → {year}")

            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_keyword_search(keyword: str) -> None:
    keyword = keyword.lower().strip()
    if not keyword:
        return

    now = datetime.utcnow()
    recent = collection.find_one({
        "type": "keyword",
        "keyword": keyword,
        "timestamp": {"$gte": now - timedelta(seconds=5)}
    })
    if not recent:
        collection.insert_one({
            "type": "keyword",
            "keyword": keyword,
            "timestamp": now
        })
        logging.info(f"Лог сохранён: keyword → '{keyword}'")


def log_genre_year_search(genres: List[str], year_from: int, year_to: int) -> None:
    genres_clean = [g.strip() for g in genres if g and g.strip()]
    if not genres_clean:
        return

    year_range = f"{year_from}–{year_to}"
    now = datetime.utcnow()
    recent = collection.find_one({
        "type": "genre_year",
        "genres": sorted(genres_clean),
        "years": year_range,
        "timestamp": {"$gte": now - timedelta(seconds=5)}
    })
    if not recent:
        collection.insert_one({
            "type": "genre_year",
            "genres": sorted(genres_clean),
            "years": year_range,
            "timestamp": now
        })
        logging.info(f"Лог сохранён: genres → {genres_clean} | years → {year_range}")


def log_genre_exact_year_search(genres: List[str], year: int) -> None:
    genres_clean = [g.strip() for g in genres if g and g.strip()]
    if not genres_clean or year is None or year < 1990:
        return

    now = datetime.utcnow()
    recent = collection.find_one({
        "type": "genre_exact_year",
        "genres": sorted(genres_clean),
        "year": year,
        "timestamp": {"$gte": now - timedelta(seconds=5)}
    })
    if not recent:
        collection.insert_one({
            "type": "genre_exact_year",
            "genres": sorted(genres_clean),
            "year": year,
            "timestamp": now
        })
        logging.info(f"Лог сохранён: genres → {genres_clean} | year → {year}")
