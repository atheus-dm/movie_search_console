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
