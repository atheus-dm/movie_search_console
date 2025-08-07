from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import logging
from functools import wraps
from typing import Callable, Any, Optional, List

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
    """
        Декоратор для логирования вызовов поисковых функций: записывает информацию о запросе в MongoDB и файл `log.txt`.

        🔧 Назначение:
            Оборачивает целевую функцию (например, поиск), чтобы автоматически сохранять логи при её вызове — без изменения самой логики функции.

        📥 Аргументы:
            log_type (str): Тип логируемого запроса — определяет поведение декоратора.
                Поддерживаемые значения:
                    - "keyword": ожидается, что первая позиция (args[0]) содержит поисковое ключевое слово — str;
                    - "genre_year": ожидается список жанров (args[0]) и диапазон лет — int от/до (args[1], args[2]);
                    - "genre_exact_year": ожидается список жанров (args[0]) и конкретный год — int (args[1]).

        🛠 Внутренняя структура:
            log_search() возвращает объект-декоратор — `decorator`.

            Функция decorator() принимает целевую функцию `func`, которую требуется обернуть.

            Она возвращает функцию-обёртку — `wrapper`, которая при каждом вызове:
                1. Проверяет наличие `logged=True` в kwargs — если такой флаг установлен, логирование пропускается. Это используется для предотвращения повторной записи в лог.
                2. Получает текущее время UTC (`now`), используемое для метки времени и проверки "свежести" запроса.
                3. В зависимости от log_type:
                    - Извлекает параметры из args: ключевое слово, жанры, годы.
                    - Очищает строковые значения (`strip()`), удаляет пустые/невалидные записи.
                    - Приводит годы к числам и фильтрует всё, что младше 1900.
                4. Выполняет поиск в MongoDB по заданным параметрам и `timestamp >= now - 5 секунд`:
                    → Это предотвращает дублирование логов при быстрой последовательной активации.
                5. Если запись не найдена:
                    - Формирует новую структуру документа (тип + параметры + метка времени);
                    - Вставляет в MongoDB через `insert_one`;
                    - Записывает сообщение в `log.txt` через `logging.info(...)`.

                6. После всех проверок и логирования, вызывает оригинальную функцию `func` с теми же аргументами:
                    → `return func(*args, **kwargs)` обеспечивает беспрепятственный вызов с возвратом результата, как будто логирования не было.

            Наконец:
            - `return wrapper` — возвращает обёртку `wrapper`, которая заменяет оригинальную функцию.
            - `return decorator` — возвращает весь декоратор, чтобы он мог быть использован как `@log_search("...")`.

        🧪 Пример использования:

            @log_search("keyword")
            def search_by_keyword(keyword: str):
                ...

            @log_search("genre_year")
            def search_by_genres(genres: List[str], from_year: int, to_year: int):
                ...

            @log_search("genre_exact_year")
            def search_by_exact_year(genres: List[str], year: int):
                ...

        📁 Структура записей в MongoDB:
            Для "keyword":
                {
                    "type": "keyword",
                    "keyword": "thriller",
                    "timestamp": <datetime>
                }

            Для "genre_year":
                {
                    "type": "genre_year",
                    "genres": ["comedy", "drama"],
                    "years": "1990–2000",
                    "timestamp": <datetime>
                }

            Для "genre_exact_year":
                {
                    "type": "genre_exact_year",
                    "genres": ["horror"],
                    "year": 1995,
                    "timestamp": <datetime>
                }

        📌 Технические замечания:
            - Все жанры сортируются (`sorted()`) — это нормализует порядок и предотвращает дубли.
            - Строки приводятся к нижнему регистру — для консистентности.
            - Вызываемая функция (`func`) остаётся полностью интактной: декоратор не изменяет её возвращаемое значение.
            - Вся логика записи отделена — облегчает повторное использование и тестирование.
        """
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
    """
        Логирует пользовательский поиск по ключевому слову в MongoDB и записывает событие в файл `log.txt`.

         Назначение:
            Используется для ручного логирования одного конкретного поискового запроса по ключевому слову —
            например, если логирование не происходит автоматически (вне декоратора) или нужно добавить событие в историю явно.

         Аргументы:
            keyword (str): Строка ключевого слова, которое вводит пользователь. Может быть жанром, названием или тематикой.

         Процесс выполнения:
            1. Очистка входной строки:
                - Приводится к нижнему регистру (`lower()`), чтобы лог был регистронезависим.
                - Удаляются пробелы по краям (`strip()`), чтобы исключить пустые или некорректные запросы.

            2. Проверка на пустоту:
                - Если после очистки строка пуста — логирование не выполняется, функция завершает работу через `return`.

            3. Получение текущего времени:
                - Используется `datetime.utcnow()` — это метка времени, которая будет записана в лог.

            4. Проверка на повторный лог (анти-дубликат):
                - Выполняется поиск в MongoDB: `collection.find_one(...)`
                - Условие:
                    - `type` должно быть `"keyword"`;
                    - `keyword` должно точно совпадать с очищенным значением;
                    - `timestamp` должен быть не старше 5 секунд (`timestamp >= now - timedelta(seconds=5)`).

            5. Если аналогичной записи не найдено:
                - Формируется и вставляется новый документ в MongoDB:
                    {
                        "type": "keyword",
                        "keyword": <очищенное значение>,
                        "timestamp": <текущее UTC время>
                    }

                - Добавляется строка в лог-файл `log.txt`:
                    Пример: `Лог сохранён: keyword → 'thriller'`

         Особенности:
            - Функция не возвращает значение (`None`) — она выполняет исключительно побочные действия: сохранение данных.
            - Механизм защиты от дублирующей записи идентичен тому, что используется в `log_search`.
            - Используется напрямую, без оборачивания других функций — удобно для сценариев вне основного pipeline (например, в админке, боте, CLI).
            - Лог-файл формируется через `logging.info(...)`, формат задан в `basicConfig()`.

         Структура записи в базе:
            {
                "type": "keyword",
                "keyword": "comedy",
                "timestamp": datetime.utcnow()
            }

         Пример:
            log_keyword_search("sci-fi")
            → создаёт запись в MongoDB и строку в log.txt, если аналогичная не была создана недавно.
        """
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
    """
        Логирует запрос поиска по жанрам и диапазону лет в MongoDB и сохраняет запись в лог-файл.

        Назначение:
            Сохраняет информацию о поисковом запросе, состоящем из одного или нескольких жанров
            и временного диапазона, при условии, что такой запрос ещё не был записан в течение последних пяти секунд.

        Аргументы:
            genres (List[str]): Список жанров, по которым осуществляется поиск.
                                Может содержать пустые или пробельные строки, которые будут исключены.
            year_from (int): Начальный год диапазона, включительно.
            year_to (int): Конечный год диапазона, включительно.

        Процесс выполнения:
            1. Очистка входных данных:
                - Каждый элемент списка genres проходит через .strip().
                - Из списка удаляются пустые строки и значения, состоящие только из пробелов.
                - Если после очистки список жанров оказался пустым — логирование не выполняется.

            2. Формирование текстового диапазона годов:
                - Годы объединяются в строку формата "YYYY–YYYY", где YYYY — значения year_from и year_to.

            3. Получение текущего времени:
                - Используется datetime.utcnow() как метка логирования.

            4. Проверка на наличие дубликата:
                - Выполняется запрос к MongoDB с условиями:
                    - type == "genre_year"
                    - genres == отсортированный genres_clean
                    - years == строка диапазона
                    - timestamp >= (текущее время - 5 секунд)
                - Если запись найдена — логирование пропускается.

            5. Если запись не найдена:
                - Создаётся новый документ:
                    {
                        "type": "genre_year",
                        "genres": sorted(genres_clean),
                        "years": "<year_from>–<year_to>",
                        "timestamp": <текущее UTC-время>
                    }
                - Документ сохраняется в коллекцию MongoDB.
                - В лог-файл `log.txt` добавляется строка через logging.info():
                    Лог сохранён: genres → <очищенные жанры> | years → <диапазон>

        Возвращаемое значение:
            None. Функция выполняет исключительно побочные эффекты — запись в MongoDB и лог-файл.

        Отличия от декоратора:
            - Не зависит от сигнатуры другой функции;
            - Может использоваться вручную в любом контексте, где необходимо явно записать лог;
            - Не поддерживает флаг `logged` — логирование всегда происходит, если нет дубликата;
            - Аргументы именованные, что упрощает вызов и повышает читаемость.
        """
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
    """
    Логирует пользовательский запрос на поиск по жанрам и конкретному году в MongoDB и лог-файл.

    Назначение:
        Используется для ручного логирования действий пользователя, связанных с фильтрацией контента по жанрам и одному конкретному году.
        Сохраняет лог-запись только в том случае, если такой запрос не был выполнен в течение последних пяти секунд.

    Аргументы:
        genres (List[str]): Список жанров, по которым осуществляется фильтрация. Допускаются пустые и пробельные строки, которые будут исключены.
        year (int): Год, по которому выполняется фильтрация. Значение должно быть целым числом не меньше 1900.

    Процесс выполнения:
        1. Очистка входных данных:
            - Все элементы списка genres проходят через .strip().
            - Пустые строки и элементы, состоящие только из пробелов, удаляются.
            - Если после очистки список жанров оказался пустым — логирование не выполняется.

        2. Валидация года:
            - Год должен быть целым числом (int) и не меньше 1900.
            - Если значение недопустимо (например, None, отрицательное, менее 1900) — логирование не выполняется.

        3. Получение текущей метки времени:
            - Используется datetime.utcnow() для фиксации времени запроса.

        4. Проверка на наличие дубликата:
            - Выполняется запрос к MongoDB, который ищет документ с полями:
                - type == "genre_exact_year";
                - genres == отсортированный genres_clean;
                - year == переданное значение года;
                - timestamp >= (текущее время - 5 секунд).
            - Если совпадающая запись найдена — логирование пропускается.

        5. Если запись не найдена:
            - Формируется новый документ:
                {
                    "type": "genre_exact_year",
                    "genres": sorted(genres_clean),
                    "year": year,
                    "timestamp": datetime.utcnow()
                }
            - Документ сохраняется в MongoDB через insert_one().
            - В лог-файл `log.txt` добавляется строка через logging.info():
                Лог сохранён: genres → <жанры> | year → <год>

    Возвращаемое значение:
        None. Функция реализует побочные действия и не возвращает результат.

    Отличия от других логирующих функций:
        - В лог сохраняется одиночный год, а не диапазон (в отличие от log_genre_year_search).
        - Требуется строгая проверка валидности года.
        - Поля `years` не используются, только `year`.
        - Механизм сортировки жанров и защита от повторов аналогичны остальным логирующим функциям.

    Пример вызова:
        log_genre_exact_year_search(['sci-fi', 'thriller'], 1999)
        → создаст запись в базе и в лог-файле, если аналогичная не была создана в течение последних 5 секунд.
    """
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
