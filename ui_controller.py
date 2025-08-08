from input_utils import (
    prompt_valid_year,
    prompt_next_page,
    select_genres,
    sanitize_input
)
from search_engine import search_by_keyword, search_by_genre_year, search_by_genre_exact_year
from formatter import (
    format_movies_table,
    format_top_keywords,
    format_top_genres,
    format_last_searches,
    format_genres_table
)
from log_stats import get_top_keywords, get_top_genres, get_last_searches
from visualizer import loading_animation, celebrate
from mysql_connector import get_year_range, get_genres_with_ids


def run_app() -> None:
    while True:
        print("\n🎬 Добро пожаловать в МувиПоиск!")
        print("1️⃣ Поиск по ключевому слову")
        print("2️⃣ Поиск по жанру и году")
        print("3️⃣ Статистика")
        print("4️⃣ Выход")

        try:
            choice = input("👉 Выберите действие: ").strip()
        except KeyboardInterrupt:
            print("\n👋 Прерывание — до встречи!")
            break

        if choice == "1":
            handle_keyword_search()

        elif choice == "2":
            handle_genre_year_search()

        elif choice == "3":
            handle_statistics()

        elif choice == "4":
            print("👋 До встречи!")
            break

        else:
            print("❌ Неверный выбор. Попробуйте снова.")


def handle_keyword_search() -> None:
    raw_input = input("🔎 Введите ключевое слово: ")
    keyword = sanitize_input(raw_input)
    if not keyword:
        print("⚠️ Пустой или некорректный ввод. Попробуйте снова.")
        return

    offset = 0
    logged = False

    while True:
        loading_animation("Ищем фильмы")
        movies = search_by_keyword(keyword, offset=offset, logged=logged)
        logged = True  # Логируем только первый запрос

        if not movies:
            print("😢 Фильмы не найдены." if offset == 0 else "📭 Больше фильмов не найдено.")
            break

        print(f"\n📦 Найдено фильмов: {len(movies)} (страница {offset // 10 + 1})")
        format_movies_table(movies)
        celebrate()

        if prompt_next_page() != "y":
            break
        offset += 10


def handle_genre_year_search() -> None:
    year_from, year_to = get_year_range()
    genres_map = get_genres_with_ids()
    genre_names = [genre["name"] for genre in genres_map]
    format_genres_table(genre_names)

    selected_genres = select_genres(genres_map)
    if not selected_genres:
        print("⚠️ Не выбран ни один жанр. Поиск отменён.")
        return

    print("\n📅 Выберите тип поиска:")
    print("1️⃣ По диапазону годов")
    print("2️⃣ По конкретному году")
    mode = input("👉 Ваш выбор: ").strip()

    if mode == "1":
        year_start = prompt_valid_year(f"📅 Введите год ОТ ({year_from} – {year_to}): ", year_from, year_to)
        year_end = prompt_valid_year(f"📅 Введите год ДО ({year_from} – {year_to}): ", year_from, year_to)

        if year_start > year_end:
            print("⚠ Год ОТ не может быть больше года ДО.")
            return

        page = 1
        logged = False

        while True:
            loading_animation("Ищем фильмы")
            result = search_by_genre_year(
                selected_genres, year_start, year_end, offset=(page - 1) * 10, logged=logged
            )
            logged = True

            movies = result.get("movies", [])
            total = result.get("total_count", 0)

            if page == 1:
                print(f"\n📦 Всего найдено: {total} фильмов")

            if not movies:
                print("📭 Больше фильмов не найдено.")
                break

            print(f"\n📦 Показано: {len(movies)} фильмов (страница {page})")
            format_movies_table(movies)
            celebrate()

            if prompt_next_page() != "y":
                break
            page += 1

    elif mode == "2":
        print(f"\n📅 Диапазон доступных годов: {year_from} – {year_to}")
        exact_year = prompt_valid_year(f"📅 Введите конкретный год ({year_from} – {year_to}): ", year_from, year_to)

        page = 1
        logged = False

        while True:
            loading_animation("Ищем фильмы")
            result = search_by_genre_exact_year(
                selected_genres, exact_year, offset=(page - 1) * 10, logged=logged
            )
            logged = True

            movies = result.get("movies", [])
            total = result.get("total_count", 0)

            if page == 1:
                print(f"\n📦 Всего найдено: {total} фильмов")

            if not movies:
                print("📭 Больше фильмов не найдено.")
                break

            print(f"\n📦 Показано: {len(movies)} фильмов (страница {page})")
            format_movies_table(movies)
            celebrate()

            if prompt_next_page() != "y":
                break
            page += 1

    else:
        print("❌ Неверный выбор. Поиск отменён.")


def handle_statistics() -> None:
    print("\n📊 Статистика поисков:")
    format_top_keywords(get_top_keywords())
    format_top_genres(get_top_genres())
    format_last_searches(get_last_searches())
