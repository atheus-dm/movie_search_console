import mysql.connector
from mysql.connector import Error, MySQLConnection
from dotenv import load_dotenv
import os
from typing import List, Dict, Tuple, Any, Optional

# 🛠 Загрузка конфигурации из .env
load_dotenv()


def create_connection() -> Optional[MySQLConnection]:
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
