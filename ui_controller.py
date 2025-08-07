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
    """
        Запускает основной цикл консольного приложения MovieSearch.

        Назначение:
            Обеспечивает взаимодействие с пользователем через текстовое меню.
            В зависимости от выбора пользователя инициирует соответствующий сценарий поиска или просмотра статистики.

        Логика выполнения:
            1. Показывается приветственное сообщение и меню выбора:
                - Поиск по ключевому слову
                - Поиск по жанру и году
                - Статистика
                - Выход из приложения

            2. Считывается ввод пользователя через `input()` и очищается от пробелов.
            3. Проверка выбранного пункта:
                - Если "1" → вызывает `handle_keyword_search()`
                - Если "2" → вызывает `handle_genre_year_search()`
                - Если "3" → вызывает `handle_statistics()`
                - Если "4" → завершает приложение
                - Иначе → сообщение об ошибке

            4. Обработка прерывания (`KeyboardInterrupt`) с корректным выходом из программы.

        Возвращаемое значение:
            None

        Пример использования:
            run_app() → Запускает главное текстовое меню приложения и ожидает действия пользователя
        """
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
    """
    Обрабатывает сценарий поиска фильмов по ключевому слову.

    Назначение:
        Позволяет пользователю выполнить полнотекстовый поиск фильмов по одному ключевому слову.
        Ввод очищается, затем запускается поиск с поддержкой постраничного вывода и логированием первого запроса.

    Логика выполнения:
        1. Получение сырых данных от пользователя через `input()`.
        2. Очистка строки (`sanitize_input`) от пробелов и потенциального мусора.
        3. Проверка валидности: если строка пуста — вывод предупреждения и завершение сценария.
        4. Инициализация параметров `offset = 0` и `logged = False`.
        5. В цикле:
            - Анимация загрузки через `loading_animation`.
            - Вызов `search_by_keyword(...)` с текущими параметрами.
            - Логирование включается только при первом запросе.
            - Если результатов нет:
                • При `offset == 0` → сообщение "Фильмы не найдены".
                • Иначе → "Больше фильмов не найдено".
                • Завершение сценария.
            - Иначе:
                • Отображение количества найденных фильмов и текущей страницы.
                • Форматированный вывод таблицы через `format_movies_table`.
                • Анимация празднования через `celebrate()`.
            - Запрос продолжения через `prompt_next_page()`.
                • Если ответ — не "y", сценарий завершается.
                • Иначе `offset += 10` и начинается следующая итерация.

    Взаимодействия:
        - Пользователь вводит строку.
        - Функция запрашивает и отображает результаты.
        - Поддерживается пагинация по 10 элементов.

    Возвращаемое значение:
        None

    Пример:
        handle_keyword_search()
        → Запрашивает ключевое слово, отображает страницы найденных фильмов, логирует первый запрос.
    """
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
    """
    Обрабатывает сценарий поиска фильмов по жанрам с выбором режима: диапазон лет или конкретный год.

    Назначение:
        Позволяет пользователю выбрать жанры и годовой критерий (интервал или точное значение),
        затем выполняет соответствующий SQL-поиск с постраничным выводом и логированием первого запроса.

    Логика выполнения:
        1. Получение справочной информации:
            - Диапазон доступных годов через `get_year_range()`.
            - Список жанров с ID через `get_genres_with_ids()` и форматированный вывод `format_genres_table()`.

        2. Выбор жанров пользователем через `select_genres(genres_map)`.
            - Если список пуст, выводится сообщение и сценарий завершается.

        3. Выбор режима поиска:
            - "1" → Поиск по диапазону лет.
                • Ввод начального и конечного года через `prompt_valid_year`.
                • Проверка, что `year_start ≤ year_end`.
                • Цикл пагинации:
                    ◦ Вызов `search_by_genre_year(...)`.
                    ◦ Логирование только при первой итерации.
                    ◦ Вывод общего количества результатов (только на первой странице).
                    ◦ Отображение текущей страницы: заголовок, таблица фильмов, анимация.
                    ◦ Переход на следующую страницу при подтверждении.

            - "2" → Поиск по конкретному году.
                • Ввод года через `prompt_valid_year`.
                • Цикл пагинации аналогичен поиску по диапазону, но используется `search_by_genre_exact_year`.

            - Любой другой ввод → сообщение о неверном выборе, завершение сценария.

    Побочные эффекты:
        - Ввод/вывод через консоль.
        - Вызов SQL-функций поиска.
        - Анимации и оформление через visualizer.

    Возвращаемое значение:
        None

    Пример:
        handle_genre_year_search()
        → Выводит жанры, запрашивает критерии, выполняет поиск по 10 фильмов на страницу.
    """
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
    """
    Выводит статистику поисковой активности пользователей.

    Назначение:
        Позволяет пользователю ознакомиться с аналитическими данными:
        самыми популярными ключевыми словами, жанрами и последними поисковыми запросами.
        Используется в качестве вспомогательного информационного раздела.

    Логика выполнения:
        1. Отображение заголовка раздела.
        2. Получение статистических данных:
            - `get_top_keywords()`: возвращает топ ключевых слов по частоте.
            - `get_top_genres()`: возвращает самые часто используемые жанры.
            - `get_last_searches()`: возвращает список последних запросов.
        3. Форматированный вывод статистики:
            - `format_top_keywords(...)`: вывод в табличном или структурированном виде.
            - `format_top_genres(...)`: аналогично.
            - `format_last_searches(...)`: отображение истории поиска.

    Взаимодействия:
        - Все данные получаются из логов, доступных через `log_stats`.
        - Пользовательский ввод не требуется.
        - Вывод осуществляется в stdout.

    Возвращаемое значение:
        None

    Пример:
        handle_statistics()
        → Показывает статистику последних и популярных запросов.
    """
    print("\n📊 Статистика поисков:")
    format_top_keywords(get_top_keywords())
    format_top_genres(get_top_genres())
    format_last_searches(get_last_searches())
