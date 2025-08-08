from typing import Callable
from input_utils import prompt_next_page
from visualizer import loading_animation, celebrate
from formatter import format_movies_table


def paginate_results(
    fetch_function: Callable[..., list],
    fetch_args: tuple,
    start_offset: int = 0,
    label: str = "Фильмы"
) -> None:
    """
        Постранично извлекает и отображает результаты, полученные от переданной функции.

        Назначение:
            Обеспечивает интерактивный вывод длинных списков с пагинацией и пользовательским подтверждением.
            Используется для консольных интерфейсов, где данные разбиваются на страницы по 10 элементов.

        Аргументы:
            fetch_function (Callable[..., list]): Функция, извлекающая результаты. Должна принимать offset как именованный аргумент.
            fetch_args (tuple): Аргументы, передаваемые в fetch_function, кроме offset.
            start_offset (int): Начальное смещение для выборки результатов. По умолчанию 0.
            label (str): Название сущности (например, "Фильмы"), отображается в заголовках страницы.

        Логика выполнения:
            1. Устанавливается `offset`, начиная со `start_offset`.
            2. В бесконечном цикле:
                - Показ анимации загрузки с `loading_animation(...)`.
                - Вызов `fetch_function(*fetch_args, offset=offset)`.
                - Если результатов нет:
                    • Если `offset == 0`, печатается "Ничего не найдено".
                    • Иначе — "Больше результатов нет".
                    • Цикл завершается.
                - Иначе:
                    • Расчитывается номер страницы: `offset // 10 + 1`.
                    • Печатается заголовок с количеством результатов и номером страницы.
                    • Вывод результатов в табличной форме через `format_movies_table`.
                    • Праздничная анимация с `celebrate()`.
                    • Вызов `prompt_next_page()`.
                    • Если ответ — не `"y"`, цикл завершается.
                    • Иначе `offset += 10`, переходим к следующей странице.

        Ограничения:
            - Функция `fetch_function` должна быть совместима с передачей аргумента `offset`.
            - Предполагается, что она возвращает список длиной до 10 элементов (или меньше).
            - Вывод осуществляется в консоль, без GUI-элементов.

        Побочные эффекты:
            - Печатает данные в stdout.
            - Запрашивает ввод пользователя через `prompt_next_page`.

        Пример:
            paginate_results(fetch_function=search_by_genre_exact_year, fetch_args=(["Drama"], 2001))
            → Пошаговый вывод страниц с фильмами 2001 года в жанре Drama.

        Возвращаемое значение:
            None. Вывод осуществляется напрямую в stdout.
        """
    offset = start_offset

    while True:
        loading_animation(f"Ищем {label.lower()}")
        results = fetch_function(*fetch_args, offset=offset)

        if not results:
            msg = "😢 Ничего не найдено." if offset == 0 else "📭 Больше результатов нет."
            print(f"\n{msg}\n")
            break

        page_num = offset // 10 + 1
        header = f"\n📦 Найдено: {len(results)} {label.lower()} (страница {page_num})\n"
        print(header)

        format_movies_table(results)
        celebrate()

        if prompt_next_page() != "y":
            break
        offset += 10
