# 🏢 Сириус.Аренда

Сервис бронирования пространств для Университета "Сириус".

---

## 📋 О проекте

**Сириус.Аренда** — это REST API для бронирования переговорных комнат и учебных пространств. Сервис позволяет:

- 📋 Управлять пространствами (создание, просмотр, редактирование, удаление)
- 📅 Бронировать пространства на конкретное время
- 🔍 Проверять доступность пространств
- 📊 Просматривать расписание

---

## 🛠️ Технологии

- **FastAPI** — веб-фреймворк
- **SQLAlchemy** — ORM для работы с БД
- **SQLite** — база данных
- **Pydantic** — валидация данных
- **Uvicorn** — ASGI сервер

---

## 🚀 Быстрый старт

## 1. Клонировать репозиторий

```bash
git clone <url-репозитория>
cd sirius-arena
```

## 2. Создать виртуальное окружение

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```
|   Примечание: Если появляется ошибка о запрете выполнения скриптов, выполните:
|   ```bash
|   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
|   ```


## 3. Установить зависимости

```bash
pip install -r requirements.txt
```

## 4. Запустить приложение

### Способ 1: Через .bat файл (Windows)⭐

Просто дважды кликните на файл run.bat в корне проекта.

### Способ 2: Через командную строку 

Введите команды из 2-го пункта, если закрыли терминал. Если не то сразу пишите:

```bash
uvicorn app.main:app --reload
```

## 5. Открыть в браузере

Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

## 📚 Документация API

### Комнаты

Метод	        URL	                Описание
GET	        /rooms/	            Список всех комнат
GET	        /rooms/available	Поиск свободных комнат
GET	        /rooms/{id}	        Детали комнаты
POST	    /rooms/	            Создать комнату
PUT	        /rooms/{id}	        Обновить комнату
DELETE	    /rooms/{id}	        Удалить комнату

#### Фильтры для GET /rooms/:

?capacity=10 — минимальная вместимость

?equipment=проектор,доска — оборудование через запятую

?require_all=true — требуется всё оборудование

#### Параметры для GET /rooms/available:

start — начало интервала (YYYY-MM-DDTHH:MM:SS)

end — конец интервала (YYYY-MM-DDTHH:MM:SS)

capacity — минимальная вместимость

equipment — список оборудования через запятую

### Бронирования

Метод	    URL	                            Описание
POST	/bookings/	                    Создать бронирование
DELETE	/bookings/{id}	                Отменить бронирование
GET	    /rooms/{id}/bookings?date=...	Расписание на день

### Оборудование

Метод	    URL	                Описание
GET	    /equipment/	        Список оборудования
POST	/equipment/	        Создать оборудование
GET	    /equipment/{id}	    Детали оборудования
PUT	    /equipment/{id}	    Обновить оборудование
DELETE	/equipment/{id}	    Удалить оборудование

## 📝 Примеры запросов

### Создание оборудования

curl -X POST http://localhost:8000/equipment/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "проектор",
    "description": "Full HD проектор"
  }'

### Создание комнаты

curl -X POST http://localhost:8000/rooms/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Переговорная А",
    "capacity": 10,
    "description": "Для переговоров",
    "equipment": [
      {"equipment_id": 1, "count": 1, "condition": "исправно"}
    ]
  }'

### Создание бронирования

curl -X POST http://localhost:8000/bookings/ \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": 1,
    "start_time": "2026-07-12T10:00:00",
    "end_time": "2026-07-12T12:00:00",
    "user_name": "Иван Петров"
  }'

### Получение расписания на день

curl "http://localhost:8000/rooms/1/bookings?date=2026-07-12"

### Поиск свободных комнат

curl "http://localhost:8000/rooms/available?start=2026-07-12T10:00:00&end=2026-07-12T12:00:00&capacity=5&equipment=проектор"

## 🧪 Тестирование

### Через Swagger UI

Откройте http://localhost:8000/docs и тестируйте прямо в браузере.

### Через curl

Проверка работоспособности:
curl http://localhost:8000/health

Получить все комнаты:
curl http://localhost:8000/rooms/

Получить комнату по ID:
curl http://localhost:8000/rooms/1

## 🗂️ Структура проекта

sirius-arena/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Точка входа
│   ├── database.py             # Подключение к БД
│   ├── models.py               # Модели SQLAlchemy
│   ├── schemas.py              # Схемы Pydantic
│   │
│   ├── repositories/           # CRUD-классы
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── room_repository.py
│   │   ├── booking_repository.py
│   │   └── equipment_repository.py
│   │
│   └── routes/                 # Эндпоинты
│       ├── __init__.py
│       ├── rooms.py
│       ├── bookings.py
│       └── equipment.py
│
│
├── requirements.txt            # Зависимости
├── run.bat                     # 🚀 Запуск одной кнопкой (Windows)
└── README.md                   # Документация

## ⚠️ Обработка ошибок

Код	        Описание
200     OK	Успешный запрос
201     Created	Объект создан
400     Bad Request	Ошибка валидации данных
404     Not Found	Объект не найден
409     Conflict	Конфликт (комната уже занята)

## 🚀 Запуск одной кнопкой (run.bat)

В корне проекта создан файл run.bat. Просто дважды кликните по нему — и приложение запустится!

### Содержимое run.bat:

@echo off
echo 🚀 Запуск Сириус.Аренда...
call venv\Scripts\activate
uvicorn app.main:app --reload
pause

## 📊 Схема базы данных

┌────────────────────┐      ┌────────────────────────┐      ┌────────────────────┐
│       rooms        │      │    room_equipment      │      │    equipment       │
├────────────────────┤      ├────────────────────────┤      ├────────────────────┤
│ id (PK)            │◄─────│ room_id (FK)           │      │ id (PK)            │
│ name               │      │ equipment_id (FK)      │─────►│ name               │
│ capacity           │      │ count                  │      │ description        │
│ description        │      │ condition              │      └────────────────────┘
└────────────────────┘      └────────────────────────┘
         │ 1
         │
         ▼ M
┌────────────────────┐
│     bookings       │
├────────────────────┤
│ id (PK)            │
│ room_id (FK)       │
│ start_time         │
│ end_time           │
│ user_name          │
│ status             │
└────────────────────┘

## 📝 Требования к системе

Python 3.11 или выше
pip (менеджер пакетов)
Git (для клонирования)

## 👤 Автор

Михаил Нерушенко

## 📄 Лицензия

Этот проект создан для участия в конкурсе «Всероссийский ИТ-раунд».