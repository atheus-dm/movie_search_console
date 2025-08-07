from mysql_connector import (
    search_by_keyword as sql_search_by_keyword,
    search_by_genre_year as sql_search_by_genre_year,
    search_by_genre_exact_year as sql_search_by_genre_exact_year
)
from log_writer import log_search
from typing import List, Dict, Any

"""
Описание:
    Обёрточный модуль, предоставляющий интерфейс поиска фильмов с логированием запросов.
    Все функции используют SQL-запросы из mysql_connector и автоматически логируются
    с помощью декоратора @log_search из log_writer.

Назначение:
    - Централизованный доступ к поисковым функциям.
    - Добавление логирования без изменения SQL-реализаций.
    - Совместимость с пагинацией и выводом результатов в консоль.

Импорт:
    from mysql_connector import (
        search_by_keyword as sql_search_by_keyword,
        search_by_genre_year as sql_search_by_genre_year,
        search_by_genre_exact_year as sql_search_by_genre_exact_year
    )
    from log_writer import log_search
    from typing import List, Dict, Any

Функции:

    @log_search("keyword")
    def search_by_keyword(keyword: str, offset: int = 0, logged: bool = False) -> List[Dict[str, Any]]:
        Выполняет SQL-поиск фильмов по ключевому слову.

        Аргументы:
            keyword (str): Поисковый термин.
            offset (int): Смещение в результатах.
            logged (bool): Используется декоратором для логирования.

        Возвращает:
            List[Dict[str, Any]]: Список фильмов в формате словарей.

    @log_search("genre_year")
    def search_by_genre_year(genres: List[str], year_from: int, year_to: int,
                              offset: int = 0, logged: bool = False) -> Dict[str, Any]:
        Выполняет SQL-поиск по списку жанров и диапазону лет.

        Аргументы:
            genres (List[str]): Жанры.
            year_from (int): Начальный год.
            year_to (int): Конечный год.
            offset (int): Смещение.
            logged (bool): Флаг логирования.

        Возвращает:
            Dict[str, Any]: {
                "movies": список найденных фильмов,
                "total_count": общее число совпадений
            }

    @log_search("genre_exact_year")
    def search_by_genre_exact_year(genres: List[str], year: int,
                                   offset: int = 0, logged: bool = False) -> Dict[str, Any]:
        Выполняет SQL-поиск по жанрам и строго одному году.

        Аргументы:
            genres (List[str]): Жанры.
            year (int): Конкретный год.
            offset (int): Смещение для пагинации.
            logged (bool): Флаг логирования.

        Возвращает:
            Dict[str, Any]: {
                "movies": список фильмов,
                "total_count": количество найденных записей
            }

Особенности:
    - Все функции совместимы с системой пагинации.
    - Логирование реализовано через обёртку log_search.
    - Возвращаемые форматы унифицированы и ожидаемы.
"""

@log_search("keyword")
def search_by_keyword(keyword: str, offset: int = 0, logged: bool = False) -> List[Dict[str, Any]]:
    """Ищет фильмы по ключевому слову через SQL, с контролем логирования."""
    return sql_search_by_keyword(keyword, offset=offset)


@log_search("genre_year")
def search_by_genre_year(
    genres: List[str],
    year_from: int,
    year_to: int,
    offset: int = 0,
    logged: bool = False
) -> Dict[str, Any]:
    """Ищет фильмы по жанру и диапазону годов через SQL, с контролем логирования."""
    return sql_search_by_genre_year(genres, year_from, year_to, offset=offset)


@log_search("genre_exact_year")
def search_by_genre_exact_year(
    genres: List[str],
    year: int,
    offset: int = 0,
    logged: bool = False
) -> Dict[str, Any]:
    """Ищет фильмы по жанру и конкретному году через SQL, с контролем логирования.

    Args:
        genres: список названий жанров.
        year: конкретный год.
        offset: смещение для пагинации.
        logged: флаг логировать ли поиск.

    Returns:
        Словарь:
            - "movies": список фильмов (dict),
            - "total_count": общее количество найденных.
    """
    return sql_search_by_genre_exact_year(genres, year, offset=offset)
