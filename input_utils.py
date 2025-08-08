from typing import List, Dict, Optional
import re


def prompt_valid_year(prompt_text: str, year_from: int, year_to: int) -> int:
    while True:
        year = input(prompt_text)
        if year.isdigit():
            year_int = int(year)
            if year_from <= year_int <= year_to:
                return year_int
        print(f"⚠ Введите корректный год ({year_from}–{year_to})")


def prompt_next_page() -> str:
    while True:
        response = input("👉 Показать следующие 10? (y/n): ").strip().lower()
        if response in ("y", "n"):
            return response
        print("⚠ Введите y или n.")


def select_genres(genres_map: List[Dict]) -> List[str]:
    valid_ids = {g["category_id"] for g in genres_map}

    while True:
        raw_input_genres = input("🎭 Введите номера жанров через запятую (или 0 для всех): ").strip()
        try:
            ids = [int(i.strip()) for i in raw_input_genres.split(",")]
        except ValueError:
            print("⚠ Ошибка ввода. Введите только числа через запятую.")
            continue

        if ids == [0]:
            return [g["name"] for g in genres_map]

        invalid = [i for i in ids if i not in valid_ids]
        if invalid:
            print(f"⚠ Жанр с номером {', '.join(map(str, invalid))} не найден. Введите корректный список.")
            continue

        return [g["name"] for g in genres_map if g["category_id"] in ids]


def sanitize_input(text: str) -> Optional[str]:
    cleaned = re.sub(r"[^\w\s\-]", "", text)  # Удаляем спецсимволы кроме пробелов и дефисов
    cleaned = cleaned.strip()
    if not cleaned or cleaned.isspace():
        return None
    return cleaned
