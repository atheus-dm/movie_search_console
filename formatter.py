from typing import List, Dict, Any
from prettytable import PrettyTable, DEFAULT
import math


def format_genres_table(genres: List[str], columns: int = 4) -> None:
    if not genres:
        print("🤷 Нет доступных жанров.")
        return

    print("\n📚 Доступные жанры:")

    rows = math.ceil(len(genres) / columns)
    matrix = [["" for _ in range(columns)] for _ in range(rows)]

    for idx, genre in enumerate(genres):
        row = idx % rows
        col = idx // rows
        matrix[row][col] = f"{idx + 1}. {genre}"

    col_widths = [max(len(matrix[row][col]) for row in range(rows)) for col in range(columns)]

    for row in matrix:
        line = "   ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row))
        print(line)


def format_movies_table(movies: List[Dict[str, Any]], page: int = 1, per_page: int = 10) -> None:
    if not movies:
        print("😢 Фильмы не найдены.")
        return

    total = len(movies)
    start = (page - 1) * per_page
    end = start + per_page
    page_movies = movies[start:end]

    table = PrettyTable()
    table.set_style(DEFAULT)
    table.field_names = ["№", "Название", "Год", "Жанр", "Возрастные ограничения", "Актёры"]
    table.align["Название"] = "c"
    table.align["Год"] = "c"
    table.align["Жанр"] = "c"
    table.align["Возрастные ограничения"] = "c"
    table.align["Актёры"] = "c"
    table.max_width["Название"] = 30
    table.max_width["Актёры"] = 60

    for idx, film in enumerate(page_movies, start=start + 1):
        title = film.get("title") or "❓"
        year = str(film.get("release_year") or "—")
        genre = film.get("genre") or "—"
        rating = film.get("rating") or "—"
        actors = film.get("actors") or []
        actors_str = ", ".join(actors) if isinstance(actors, list) else str(actors)

        table.add_row([idx, title, year, genre, rating, actors_str])

    print(table)


def format_top_keywords(keywords: List[Dict[str, Any]]) -> None:
    if not keywords:
        print("🤷 Нет популярных ключевых слов.")
        return

    print("\n🔍 Топ ключевых слов:")
    for item in keywords:
        word = item.get("_id")
        if not word or str(word).strip() in ("❓", "—"):
            continue
        count = item.get("count") or 0
        print(f"   ➡️ {str(word).strip()} — {count} раз")


def format_top_genres(genres: List[Dict[str, Any]]) -> None:
    if not genres:
        print("🤷 Нет популярных жанров.")
        return

    print("\n🎬 Топ жанров:")
    for item in genres:
        genre = item.get("_id")
        if not genre or str(genre).strip() in ("❓", "—"):
            continue
        count = item.get("count") or 0
        print(f"   ➡️ {str(genre).strip()} — {count} раз")


def format_last_searches(logs: List[Dict[str, Any]]) -> None:
    if not logs:
        print("📭 История пуста.")
        return

    print("\n🕓 Последние поиски:")
    for log in logs:
        ts = log.get("timestamp")
        ts_fmt = ts.strftime("%Y-%m-%d %H:%M") if ts else "—"

        if log.get("type") == "keyword":
            keyword = str(log.get("keyword") or "—").strip()
            print(f"   🔎 По ключу: {keyword} ({ts_fmt})")

        elif log.get("type") == "genre_year":
            genres = ", ".join([g for g in log.get("genres", []) if g and g.strip()])
            year_range = str(log.get("years")).strip() if "years" in log else "—"
            print(f"   🎭 По жанрам: {genres} | Годы: {year_range} ({ts_fmt})")

        elif log.get("type") == "genre_exact_year":
            genres = ", ".join([g for g in log.get("genres", []) if g and g.strip()])
            year = log.get("year")
            year_display = str(year) if isinstance(year, int) and year > 0 else "—"
            print(f"   🎯 По жанрам: {genres} | Год: {year_display} ({ts_fmt})")

        else:
            print(f"   ❓ Неизвестный тип запроса ({ts_fmt})")
