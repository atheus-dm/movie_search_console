
---

## Movie Search Console App

Консольное Python-приложение для поиска фильмов в базе данных MySQL (Sakila).  
Приложение логирует запросы в MongoDB и файл, поддерживает пагинацию, визуальные эффекты, проверку ввода и выдаёт статистику по запросам.


### Структура проекта

| Файл                 | Назначение                                      |
|----------------------|-------------------------------------------------|
| main.py              | Точка входа                                     |
| ui_controller.py     | Интерфейс пользователя                          |
| search_engine.py     | Поисковая логика и декораторы логирования       |
| mysql_connector.py   | Работа с базой данных                           |
| log_writer.py        | Логирование (MongoDB + файл)                    |
| log_stats.py         | Анализ логов и статистика                       |
| input_utils.py       | Проверка и очистка пользовательского ввода      |
| formatter.py         | Форматированный вывод через PrettyTable         |
| pagination.py        | Постраничный вывод                              |
| visualizer.py        | Визуальные эффекты                              |
| .env                 | Переменные окружения                            |
| requirements.txt     | Зависимости                                     |
| log.txt              | Файл логов                                      |
| readme.md            | Документация проекта                            |

---

### Установка

1. Установи Python версии 3.13 или выше  
2. Установи зависимости:

```
pip install -r requirements.txt
```

3. Создай файл `.env`:

```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=sakila

MONGO_URI=mongodb://localhost:27017
MONGO_DB=movie_logs
MONGO_COLLECTION=final_project_collection
```

---

### Запуск

```
python main.py
```

---

### Функциональность

- Поиск фильмов по ключевому слову
- Расширенный поиск по жанру и диапазону годов или по жанрам и конкретному году
- Постраничный вывод результатов
- Визуальные эффекты в CLI
- Логирование в MongoDB и файл
- Генерация статистики по запросам:
  - Частые ключевые слова
  - Популярные жанры
  - Временные интервалы

---

### Зависимости

```
colorama==0.4.6
mysql-connector-python==9.4.0
pymongo==4.13.2
python-dotenv==1.1.1
prettytable>=3.9.0
```

---

### Автор [Dmitriy Chumachenko](https://www.linkedin.com/in/dmitriy-chumachenko)

