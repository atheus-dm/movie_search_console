import mysql.connector
from mysql.connector import Error, MySQLConnection
from dotenv import load_dotenv
import os
from typing import List, Dict, Tuple, Any, Optional

# 🛠 Загрузка конфигурации из .env
load_dotenv()


def create_connection() -> Optional[MySQLConnection]:
    """
    Создаёт и возвращает объект подключения к базе данных MySQL на основе конфигурации из переменных окружения.

    Назначение:
        Предоставляет единый способ инициализации соединения с MySQL,
        используемый всеми функциями модуля для выполнения SQL-запросов.

    Источники конфигурации:
        - MYSQL_HOST: адрес сервера базы данных (например, "localhost");
        - MYSQL_PORT: порт подключения (обычно 3306);
        - MYSQL_USER: имя пользователя;
        - MYSQL_PASSWORD: пароль пользователя;
        - MYSQL_DATABASE: имя целевой базы данных.

    Логика выполнения:
        1. Загружает переменные окружения из `.env`, если они ещё не загружены.
        2. Вызывает `mysql.connector.connect(...)`, передавая значения параметров из `os.getenv(...)`.
        3. В случае успешного подключения возвращает объект `MySQLConnection`.
        4. Если возникает исключение (`mysql.connector.Error`), выводит сообщение об ошибке в консоль и возвращает `None`.

    Возвращаемое значение:
        Optional[MySQLConnection]:
            - Объект подключения при успешной инициализации.
            - None, если возникла ошибка при подключении (например, неверные параметры, недоступный сервер и т.д.)."""
    try:
        return mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            port=int(os.getenv("MYSQL_PORT")),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE")
        )
    except Error as e:
        print(f"[Ошибка подключения]: {e}")
        return None


def search_by_keyword(keyword: str, offset: int = 0) -> List[Dict[str, Any]]:
    """
        Выполняет полнотекстовый поиск фильмов в базе данных MySQL по ключевому слову,
        используя условие LIKE на поле `title`. Возвращает список фильмов с агрегированными жанрами и актёрами.

        Назначение:
            Предоставляет результаты поиска по названию фильма,
            возвращая расширенную информацию о каждом фильме, включая описание, год, рейтинг, жанры и актёров.

        Аргументы:
            keyword (str): Ключевое слово, по которому выполняется поиск.
                           Используется в шаблоне LIKE: `f.title LIKE %keyword%`.
            offset (int): Смещение для пагинации. Используется в SQL как `OFFSET`, чтобы получать следующую порцию результатов.
                          Например, offset=0 — первые 10 записей, offset=10 — следующие 10 и т.д.

        Логика выполнения:
            1. Устанавливается соединение с базой данных с помощью `create_connection()`:
                - Если подключение не удалось (None), функция возвращает пустой список.

            2. Создаётся курсор с опцией `dictionary=True`,
               чтобы строки результатов автоматически преобразовывались в словари (dict), а не кортежи.

            3. SQL-запрос:
                - Выбирает из таблицы `film` основные поля:
                    - `title`, `description`, `release_year`, `rating`
                - Агрегирует связанные жанры:
                    - Через `GROUP_CONCAT(DISTINCT c.name)` — объединяет все связанные жанры через запятую
                - Агрегирует имена актёров:
                    - Через `GROUP_CONCAT(DISTINCT CONCAT(a.first_name, ' ', a.last_name))`
                - JOIN’ы:
                    - `film_category`, `category`, `film_actor`, `actor` — обеспечивают доступ к жанрам и актёрам.
                - WHERE-условие:
                    - `f.title LIKE %keyword%` — выполняется поиск по подстроке в названии.
                - Группировка:
                    - `GROUP BY f.film_id` — необходимо для работы с агрегирующими функциями.
                - Пагинация:
                    - `LIMIT 10 OFFSET {offset}` — ограничивает количество записей на одной странице (10 штук).

            4. Параметры `keyword` и `offset` передаются в `cursor.execute(...)` как плейсхолдеры `%s`,
               что защищает от SQL-инъекций.

            5. В случае успешного выполнения:
                - `cursor.fetchall()` возвращает список словарей, каждый представляет один фильм и его данные.

            6. Если возникает исключение:
                - Ошибка печатается в консоль через `print(...)`, и функция возвращает пустой список.

            7. В блоке finally:
                - Закрываются курсор и соединение, чтобы освободить ресурсы.

        Структура каждого результата:
            {
                'title': str,
                'description': str,
                'release_year': int,
                'rating': str,
                'genre': str,         # жанры через запятую (например: "Action, Comedy")
                'actors': str         # имена актёров через запятую (например: "Tom Hanks, Meg Ryan")
            }

        Возвращаемое значение:
            List[Dict[str, Any]]: Список фильмов, удовлетворяющих условиям поиска. Если подключение или запрос не удалось — возвращается [].

        Пример использования:
            search_by_keyword("Matrix", offset=0)
            → вернёт список первых 10 фильмов, где заголовок содержит "Matrix" (без учёта регистра), с агрегированными жанрами и актёрами.
        """
    connection = create_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT 
                f.title,
                f.description,
                f.release_year,
                f.rating,
                GROUP_CONCAT(DISTINCT c.name SEPARATOR ', ') AS genre,
                GROUP_CONCAT(DISTINCT CONCAT(a.first_name, ' ', a.last_name) SEPARATOR ', ') AS actors
            FROM film f
            LEFT JOIN film_category fc ON f.film_id = fc.film_id
            LEFT JOIN category c ON fc.category_id = c.category_id
            LEFT JOIN film_actor fa ON f.film_id = fa.film_id
            LEFT JOIN actor a ON fa.actor_id = a.actor_id
            WHERE f.title LIKE %s
            GROUP BY f.film_id
            LIMIT 10 OFFSET %s;
        """
        cursor.execute(query, (f"%{keyword}%", offset))
        return cursor.fetchall()
    except Error as e:
        print(f"[Ошибка запроса]: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_year_range() -> Tuple[int, int]:
    """
        Получает минимальный и максимальный год релиза среди всех фильмов в базе данных MySQL.

        Назначение:
            Предоставляет границы доступного диапазона лет релиза фильмов,
            используемые для фильтрации или отображения допустимых значений в интерфейсе.

        Аргументы:
            Отсутствуют.

        Логика выполнения:
            1. Устанавливается подключение к базе данных через `create_connection()`.
                - Если соединение не удалось установить, возвращается значение по умолчанию: (1990, 2025).

            2. Создаётся курсор и выполняется SQL-запрос:
                SELECT MIN(release_year), MAX(release_year) FROM film;

                - MIN(release_year): находит самый ранний год выхода фильма.
                - MAX(release_year): находит самый поздний год выхода фильма.

            3. Результат извлекается через `cursor.fetchone()`:
                - Возвращает кортеж (min_year, max_year).
                - Если результат отсутствует (None) — возвращается значение по умолчанию.

            4. В случае исключения:
                - Ошибка выводится в консоль.
                - Возвращается значение по умолчанию: (1990, 2025).

            5. В любом случае соединение и курсор закрываются через `finally`.

        Возвращаемое значение:
            Tuple[int, int]: Кортеж из двух целых чисел:
                - Первый элемент — минимальный год релиза (включительно).
                - Второй элемент — максимальный год релиза (включительно).
                - Значения по умолчанию: (1990, 2025) — используются при ошибке подключения или запросе.

        Особенности:
            - Значения формируются на основе таблицы `film`, поле `release_year`.
            - Может использоваться в UI-компонентах (например, селекторах года), фильтрации, аналитике.
            - Гарантирует возврат допустимого диапазона даже в случае сбоев на уровне БД.

        Пример:
            year_min, year_max = get_year_range()
            → (2001, 2022)
        """
    connection = create_connection()
    if not connection:
        return (1990, 2025)

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT MIN(release_year), MAX(release_year) FROM film;")
        result = cursor.fetchone()
        return result if result else (1990, 2025)
    except Error as e:
        print(f"[Ошибка запроса]: {e}")
        return (1990, 2025)
    finally:
        cursor.close()
        connection.close()


def get_genres() -> List[str]:
    """
        Извлекает список всех жанров из таблицы `category` в базе данных MySQL, отсортированных по алфавиту.

        Назначение:
            Предоставляет упорядоченный перечень жанров, доступных в базе данных,
            используемый для фильтрации, интерфейса, автодополнения и других операций, связанных с категоризацией контента.

        Аргументы:
            Отсутствуют.

        Логика выполнения:
            1. Устанавливается подключение к базе через `create_connection()`.
                - Если соединение не удалось (None), возвращается пустой список.

            2. Создаётся курсор (обычный, не словарный) и выполняется SQL-запрос:
                SELECT name FROM category ORDER BY name;
                - Извлекаются значения поля `name` — название жанра.
                - Сортировка по `ORDER BY name` обеспечивает алфавитный порядок.

            3. Результат извлекается через `cursor.fetchall()`, возвращающий список кортежей.
                - Каждый кортеж содержит одно значение — имя жанра.

            4. Список преобразуется через list comprehension:
                - `[row[0] for row in cursor.fetchall()]` — преобразование списка кортежей в список строк.

            5. В случае возникновения ошибки (например, сбой запроса или потери соединения):
                - Ошибка выводится в консоль.
                - Возвращается пустой список.

            6. В блоке finally:
                - Курсор и соединение закрываются вручную для освобождения ресурсов.

        Возвращаемое значение:
            List[str]: Список строк, каждая — название жанра, отсортированное по алфавиту.
                       При ошибке или отсутствии данных возвращается пустой список.

        Структура данных:
            ['Action', 'Comedy', 'Drama', 'Horror', 'Sci-Fi', ...]

        Особенности:
            - Не удаляет дубликаты — если в таблице `category` они присутствуют, они останутся в результате.
            - Работает только с жанрами, присутствующими в самой таблице `category`, без проверки использования в фильмах.
            - В отличие от `get_genres_with_ids`, возвращает только названия, без идентификаторов.

        Пример:
            genres = get_genres()
            → ['Adventure', 'Animation', 'Biography', ...]
        """
    connection = create_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM category ORDER BY name;")
        return [row[0] for row in cursor.fetchall()]
    except Error as e:
        print(f"[Ошибка запроса]: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_genres_with_ids() -> List[Dict[str, Any]]:
    """
    Извлекает список всех жанров из базы данных MySQL, которые реально используются в фильмах,
    включая их уникальные идентификаторы (category_id). Жанры отсортированы по названию.

    Назначение:
        Предоставляет структуру жанров, пригодную для отображения, фильтрации и передачи в интерфейс,
        когда требуется как имя жанра, так и его ID — например, для построения выпадающих списков или API.

    Аргументы:
        Отсутствуют.

    Логика выполнения:
        1. Устанавливается подключение к базе данных через `create_connection()`.
            Если подключение не удалось — функция возвращает пустой список.

        2. Создаётся словарный курсор (dictionary=True), обеспечивающий возврат строк в виде словарей.

        3. Выполняется SQL-запрос:
            SELECT DISTINCT c.category_id, c.name
            FROM category c
            JOIN film_category fc ON c.category_id = fc.category_id
            GROUP BY c.category_id, c.name
            ORDER BY c.name;

            Детали:
            - JOIN с таблицей `film_category` исключает жанры, не связанные ни с одним фильмом.
            - DISTINCT + GROUP BY устраняет дублирующие пары (category_id, name).
            - ORDER BY сортирует результат по имени жанра по алфавиту.

        4. Результат извлекается через `cursor.fetchall()` — список словарей со структурой:
            {
                "category_id": int,
                "name": str
            }

        5. При возникновении ошибки:
            - Выводится сообщение об ошибке.
            - Возвращается пустой список.

        6. Независимо от результата, соединение и курсор закрываются вручную в блоке `finally`.

    Возвращаемое значение:
        List[Dict[str, Any]]:
            Список словарей, каждый содержит:
                - 'category_id': уникальный идентификатор жанра;
                - 'name': название жанра.

    Особенности:
        - В отличие от функции `get_genres`, исключаются жанры, не ассоциированные с фильмами;
        - Возвращаемые ID могут использоваться в системах, где требуется хранить жанры в связанной форме;
        - Сортировка по названию делает результат предсказуемым и пригодным для UI.

    Пример:
        [
            {"category_id": 3, "name": "Action"},
            {"category_id": 7, "name": "Comedy"},
            ...
        ]
    """
    connection = create_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT DISTINCT c.category_id, c.name
            FROM category c
            JOIN film_category fc ON c.category_id = fc.category_id
            GROUP BY c.category_id, c.name
            ORDER BY c.name;
        """
        cursor.execute(query)
        return cursor.fetchall()
    except Error as e:
        print(f"[Ошибка запроса]: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def search_by_genre_year(
    genres: List[str],
    year_from: int,
    year_to: int,
    offset: int = 0
) -> Dict[str, Any]:
    """
        Выполняет поиск фильмов по жанрам и диапазону лет, используя два SQL-запроса:
        один для подсчёта общего количества совпадений, второй — для извлечения текущей порции результатов с пагинацией.

        Назначение:
            Предоставляет интерфейс для фильтрации фильмов по выбранным жанрам и диапазону лет выпуска.
            Используется при построении страниц с результатами поиска, включая поддержку пагинации.

        Аргументы:
            genres (List[str]): Список жанров, по которым фильтруются фильмы. Значения очищаются от пробелов.
            year_from (int): Нижняя граница диапазона лет релиза (включительно).
            year_to (int): Верхняя граница диапазона лет релиза (включительно).
            offset (int): Смещение для пагинации. Например, offset=0 — первая страница, offset=10 — вторая и т.д.

        Логика выполнения:
            1. Подключается к базе данных через `create_connection()`.
                - Если соединение не удалось — функция возвращает {"movies": [], "total_count": 0}.

            2. Создаёт словарный курсор (`dictionary=True`) для получения результатов как словарей.

            3. Очищает список жанров:
                - Применяется `.strip()` к каждому элементу.
                - Пустые строки отфильтровываются.
                - Если результат — пустой список, оба запроса завершатся пустым результатом.

            4. Формирует SQL-плейсхолдеры:
                - `%s` умножается на количество жанров: `'Sci-Fi', 'Action'` → `(%s, %s)`

            5. Подсчёт количества совпадающих фильмов:
                - Выполняется отдельный SQL-запрос (`count_query`) с использованием подзапроса.
                - Условия:
                    - `category.name IN (%s, ...)`
                    - `release_year BETWEEN year_from AND year_to`
                - Подсчёт количества осуществляется через `COUNT(*)` во вложенном запросе.

            6. Поиск списка фильмов:
                - Второй SQL-запрос (`film_query`) выбирает детальные данные по фильмам:
                    - `title`, `description`, `release_year`, `rating`
                    - агрегированные жанры через `GROUP_CONCAT`
                    - агрегированные актёры через `GROUP_CONCAT(CONCAT(...))`
                - JOIN’ы:
                    - `film_category`, `category` (для жанров)
                    - `film_actor`, `actor` (для актёров)
                - Условия:
                    - Жанры в списке
                    - Годы в диапазоне
                - Пагинация через `LIMIT 10 OFFSET %s`.
                - Группировка по `film_id` обязательна для использования агрегирующих функций.

            7. Обработка результатов:
                - Сначала извлекается `total_count` из `count_query`.
                - Затем извлекается список фильмов из `film_query`.

            8. Оборачивает результат в структуру:
                {
                    "movies": [...],       # Список словарей с информацией о фильмах
                    "total_count": int     # Общее количество найденных записей по критериям
                }

            9. При возникновении ошибки на любом этапе:
                - Исключение обрабатывается, печатается сообщение.
                - Возвращается {"movies": [], "total_count": 0}.

            10. В блоке finally:
                - Курсор и соединение закрываются вручную.

        Возвращаемое значение:
            Dict[str, Any]:
                - "movies": список фильмов с полями:
                    - title: str
                    - description: str
                    - release_year: int
                    - rating: str
                    - genre: str (агрегированные жанры через запятую)
                    - actors: str (агрегированные актёры через запятую)
                - "total_count": общее количество совпадающих фильмов (int)

        Пример:
            result = search_by_genre_year(["Drama", "Comedy"], 2000, 2010, offset=20)
            → result["movies"]: список фильмов с 3-й страницы
            → result["total_count"]: общее число найденных фильмов за 2000–2010
        """
    connection = create_connection()
    if not connection:
        return {"movies": [], "total_count": 0}

    try:
        cursor = connection.cursor(dictionary=True)
        genres_clean = [g.strip() for g in genres if g.strip()]
        genre_placeholder = ','.join(['%s'] * len(genres_clean))

        count_query = f'''
            SELECT COUNT(*) AS total FROM (
                SELECT f.film_id
                FROM film f
                JOIN film_category fc ON f.film_id = fc.film_id
                JOIN category c ON fc.category_id = c.category_id
                WHERE c.name IN ({genre_placeholder})
                AND f.release_year BETWEEN %s AND %s
                GROUP BY f.film_id
            ) AS subquery;
        '''
        cursor.execute(count_query, (*genres_clean, year_from, year_to))
        total_count = cursor.fetchone()["total"]

        film_query = f'''
            SELECT
                f.title,
                f.description,
                f.release_year,
                f.rating,
                GROUP_CONCAT(DISTINCT c.name SEPARATOR ', ') AS genre,
                GROUP_CONCAT(DISTINCT CONCAT(a.first_name, ' ', a.last_name) SEPARATOR ', ') AS actors
            FROM film f
            JOIN film_category fc ON f.film_id = fc.film_id
            JOIN category c ON fc.category_id = c.category_id
            LEFT JOIN film_actor fa ON f.film_id = fa.film_id
            LEFT JOIN actor a ON fa.actor_id = a.actor_id
            WHERE c.name IN ({genre_placeholder})
            AND f.release_year BETWEEN %s AND %s
            GROUP BY f.film_id
            LIMIT 10 OFFSET %s;
        '''
        cursor.execute(film_query, (*genres_clean, year_from, year_to, offset))
        movies = cursor.fetchall()

        return {
            "movies": movies,
            "total_count": total_count
        }

    except Error as e:
        print(f"[Ошибка запроса]: {e}")
        return {"movies": [], "total_count": 0}
    finally:
        cursor.close()
        connection.close()


def search_by_genre_exact_year(
    genres: List[str],
    year: int,
    offset: int = 0
) -> Dict[str, Any]:
    """
        Выполняет поиск фильмов по выбранным жанрам и одному конкретному году,
        возвращая как список результатов, так и общее количество совпадений.

        Назначение:
            Обеспечивает точечный фильтр по жанру и году выпуска.
            Используется в сценариях, когда необходимо получить фильмы, вышедшие строго в заданный год, относящиеся к заданным жанрам.

        Аргументы:
            genres (List[str]): Список жанров для фильтрации. Элементы очищаются от пробелов; пустые строки исключаются.
            year (int): Год выпуска фильма, по которому выполняется фильтрация (например, 1999).
            offset (int): Смещение для пагинации. Используется в SQL-условии OFFSET, чтобы получить нужную страницу результатов.

        Логика выполнения:
            1. Устанавливается соединение с базой данных через `create_connection()`.
               При неудаче возвращается {"movies": [], "total_count": 0}.

            2. Создаётся словарный курсор (`dictionary=True`) для возврата результатов в виде списка словарей.

            3. Подготавливаются входные данные:
                - Жанры очищаются и фильтруются. Если список пуст — запрос всё равно будет выполнен, но может вернуть пустой результат.
                - Формируются SQL-плейсхолдеры `%s` для всех жанров: 'Action', 'Drama' → (%s, %s)

            4. Первый SQL-запрос (`count_query`) выполняет подсчёт общего числа совпадений:
                - Поиск по таблицам `film`, `film_category`, `category`
                - Условие: `c.name IN (...)` и `f.release_year = year`
                - Используется вложенный запрос с `GROUP BY film_id`, чтобы избежать дубликатов.

            5. Второй SQL-запрос (`film_query`) возвращает подробные данные о фильмах:
                - Извлекаются поля: title, description, release_year, rating
                - Агрегированные жанры через `GROUP_CONCAT(DISTINCT c.name)`
                - Агрегированные актёры через `GROUP_CONCAT(DISTINCT CONCAT(...))`
                - JOIN’ы с таблицами актёров и категорий
                - Группировка по `film_id` обязательна для работы агрегатов
                - Пагинация реализуется через `LIMIT 10 OFFSET %s`

            6. Результаты:
                - Сначала извлекается `total_count` из первого запроса;
                - Затем извлекается список фильмов из второго запроса.

            7. Возврат результата в виде словаря:
                {
                    "movies": [...],       # список словарей с данными по фильмам
                    "total_count": int     # общее число совпадающих записей
                }

            8. В случае возникновения исключений:
                - Печатается сообщение об ошибке.
                - Возвращается {"movies": [], "total_count": 0}.

            9. В завершение соединение и курсор закрываются в блоке `finally`.

        Формат одного элемента результата:
            {
                "title": str,
                "description": str,
                "release_year": int,
                "rating": str,
                "genre": str,       # строка жанров, разделённых запятой
                "actors": str       # строка имён актёров, разделённых запятой
            }

        Возвращаемое значение:
            Dict[str, Any]: Словарь с двумя ключами:
                - "movies": список фильмов (до 10 записей в зависимости от offset)
                - "total_count": общее количество подходящих фильмов

        Пример:
            result = search_by_genre_exact_year(['Drama', 'Thriller'], 1999)
            → result["movies"]: список фильмов 1999 года по этим жанрам
            → result["total_count"]: число всех совпадений по этим критериям
        """
    connection = create_connection()
    if not connection:
        return {"movies": [], "total_count": 0}

    try:
        cursor = connection.cursor(dictionary=True)
        genres_clean = [g.strip() for g in genres if g.strip()]
        genre_placeholder = ','.join(['%s'] * len(genres_clean))

        count_query = f'''
            SELECT COUNT(*) AS total FROM (
                SELECT f.film_id
                FROM film f
                JOIN film_category fc ON f.film_id = fc.film_id
                JOIN category c ON fc.category_id = c.category_id
                WHERE c.name IN ({genre_placeholder})
                AND f.release_year = %s
                GROUP BY f.film_id
            ) AS subquery;
        '''
        cursor.execute(count_query, (*genres_clean, year))
        total_count = cursor.fetchone()["total"]

        film_query = f'''
            SELECT
                f.title,
                f.description,
                f.release_year,
                f.rating,
                GROUP_CONCAT(DISTINCT c.name SEPARATOR ', ') AS genre,
                GROUP_CONCAT(DISTINCT CONCAT(a.first_name, ' ', a.last_name) SEPARATOR ', ') AS actors
            FROM film f
            JOIN film_category fc ON f.film_id = fc.film_id
            JOIN category c ON fc.category_id = c.category_id
            LEFT JOIN film_actor fa ON f.film_id = fa.film_id
            LEFT JOIN actor a ON fa.actor_id = a.actor_id
            WHERE c.name IN ({genre_placeholder})
            AND f.release_year = %s
            GROUP BY f.film_id
            LIMIT 10 OFFSET %s;
        '''
        cursor.execute(film_query, (*genres_clean, year, offset))
        movies = cursor.fetchall()

        return {
            "movies": movies,
            "total_count": total_count
        }

    except Error as e:
        print(f"[Ошибка запроса]: {e}")
        return {"movies": [], "total_count": 0}
    finally:
        cursor.close()
        connection.close()
