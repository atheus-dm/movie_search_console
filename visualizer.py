import time
from typing import List

try:
    import winsound  # Для Windows beep
except ImportError:
    winsound = None


def loading_animation(message: str = "Поиск") -> None:
    """
        Отображает простую анимацию загрузки с последовательным добавлением точек,
        имитируя процесс ожидания, и завершает выводом сообщения и звуковым сигналом.

        Назначение:
            Используется для создания визуальной обратной связи при выполнении поиска
            или любой операции, требующей времени. Повышает интерактивность консольного интерфейса.

        Аргументы:
            message (str): Строка, отображаемая перед точками (по умолчанию "Поиск").

        Логика выполнения:
            1. Цикл из 3 итераций (i от 0 до 2):
                - Создаются точки: "." * (i + 1)
                - Строка форматируется как: `message + точки + пробелы для выравнивания`
                - Вывод через `print(..., end="\r")` для перезаписи строки
                - Пауза 0.5 секунды через `time.sleep(0.5)`
            2. После цикла:
                - Выводится финальное сообщение "✅ Поиск завершён!"
                - Воспроизводится звуковой сигнал через `play_success_sound()`

        Зависимости:
            - `time.sleep` для задержки
            - `sys.stdout` не используется явно, но вывод реализуется через `print(..., end="\r")`
            - `play_success_sound()` вызывается по завершении

        Возвращаемое значение:
            None

        Пример:
            loading_animation("Загружаем данные")
            → Показывает "Загружаем данные." → "Загружаем данные.." → "Загружаем данные..."
               → "✅ Поиск завершён!" → воспроизводится звуковой сигнал
        """
    for i in range(3):
        dots = "." * (i + 1)
        print(f"{message}{dots}{' ' * (2 - i)}", end="\r")
        time.sleep(0.5)
    print("✅ Поиск завершён!")
    play_success_sound()


def highlight_text(text: str) -> None:
    border = "=" * (len(text) + 4)
    print(border)
    print(f"| {text} |")
    print(border)


def celebrate() -> None:
    fireworks = ["🎆", "✨", "🔥", "💥"]
    print("🎉 Ура! Всё получилось!", end=" ")
    for i in range(6):
        print(fireworks[i % len(fireworks)], end=" ")
        time.sleep(0.2)
    print()
    play_success_sound()


def print_error(message: str) -> None:
    print(f"⚠ {message}")
    play_error_sound()


def print_success(message: str) -> None:
    print(f"✅ {message}")
    play_success_sound()


def play_success_sound() -> None:
    if winsound:
        winsound.Beep(1200, 150)
    else:
        print("(звук: ✅ beep)")


def play_error_sound() -> None:
    if winsound:
        winsound.Beep(400, 300)
    else:
        print("(звук: ⚠ beep)")
