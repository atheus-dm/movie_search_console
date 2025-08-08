from mysql_connector import (
    search_by_keyword as sql_search_by_keyword,
    search_by_genre_year as sql_search_by_genre_year,
    search_by_genre_exact_year as sql_search_by_genre_exact_year
)
from log_writer import log_search
from typing import List, Dict, Any

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
