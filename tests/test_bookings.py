import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from datetime import datetime, timedelta

# ============================================
# НАСТРОЙКА ТЕСТОВОЙ БАЗЫ ДАННЫХ
# ============================================

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_room():
    """Создаём тестовую комнату"""
    response = client.post("/rooms/", json={
        "name": "Комната для бронирования",
        "capacity": 10,
        "description": "Для тестов бронирования",
        "equipment": []
    })
    return response.json()

# ============================================
# ТЕСТ 1: СОЗДАНИЕ БРОНИРОВАНИЯ
# ============================================

def test_create_booking(test_room):
    """Тест создания бронирования"""
    room_id = test_room["id"]
    
    start_time = (datetime.now() + timedelta(days=1)).isoformat()
    end_time = (datetime.now() + timedelta(days=1, hours=2)).isoformat()
    
    response = client.post("/bookings/", json={
        "room_id": room_id,
        "start_time": start_time,
        "end_time": end_time,
        "user_name": "Тестовый пользователь"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert data["room_id"] == room_id
    assert data["user_name"] == "Тестовый пользователь"
    assert data["status"] == "активно"

# ============================================
# ТЕСТ 2: КОНФЛИКТ БРОНИРОВАНИЙ
# ============================================

def test_booking_conflict(test_room):
    """Тест: нельзя забронировать занятую комнату"""
    room_id = test_room["id"]
    
    start_time = (datetime.now() + timedelta(days=1)).isoformat()
    end_time = (datetime.now() + timedelta(days=1, hours=2)).isoformat()
    
    # Шаг 1: Создаём первое бронирование
    booking1 = client.post("/bookings/", json={
        "room_id": room_id,
        "start_time": start_time,
        "end_time": end_time,
        "user_name": "Иван"
    })
    assert booking1.status_code == 201
    
    # Шаг 2: Пытаемся создать пересекающееся бронирование
    conflict_start = (datetime.now() + timedelta(days=1, minutes=30)).isoformat()
    conflict_end = (datetime.now() + timedelta(days=1, hours=2, minutes=30)).isoformat()
    
    booking2 = client.post("/bookings/", json={
        "room_id": room_id,
        "start_time": conflict_start,
        "end_time": conflict_end,
        "user_name": "Петр"
    })
    
    # Шаг 3: Проверяем конфликт
    assert booking2.status_code == 409  # Conflict!
    error_data = booking2.json()
    assert "already booked" in str(error_data).lower() or "занята" in str(error_data)

# ============================================
# ТЕСТ 3: ОТМЕНА БРОНИРОВАНИЯ
# ============================================

def test_cancel_booking(test_room):
    """Тест отмены бронирования"""
    room_id = test_room["id"]
    
    start_time = (datetime.now() + timedelta(days=1)).isoformat()
    end_time = (datetime.now() + timedelta(days=1, hours=2)).isoformat()
    
    # Шаг 1: Создаём бронирование
    booking = client.post("/bookings/", json={
        "room_id": room_id,
        "start_time": start_time,
        "end_time": end_time,
        "user_name": "Иван"
    })
    assert booking.status_code == 201
    booking_id = booking.json()["id"]
    
    # Шаг 2: Отменяем бронирование
    response = client.delete(f"/bookings/{booking_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "отменено"
    
    # Шаг 3: Проверяем, что бронирование отменено
    # (не должно показываться в расписании)
    date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    schedule = client.get(f"/rooms/{room_id}/bookings?date={date_str}")
    assert schedule.status_code == 200
    bookings = schedule.json()
    # Отменённое бронирование не должно быть в списке
    assert len(bookings) == 0

# ============================================
# ТЕСТ 4: РАСПИСАНИЕ НА ДЕНЬ
# ============================================

def test_get_schedule(test_room):
    """Тест получения расписания на день"""
    room_id = test_room["id"]
    
    # Шаг 1: Создаём несколько бронирований на один день
    date_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    booking1 = client.post("/bookings/", json={
        "room_id": room_id,
        "start_time": f"{date_str}T10:00:00",
        "end_time": f"{date_str}T12:00:00",
        "user_name": "Иван"
    })
    assert booking1.status_code == 201
    
    booking2 = client.post("/bookings/", json={
        "room_id": room_id,
        "start_time": f"{date_str}T14:00:00",
        "end_time": f"{date_str}T16:00:00",
        "user_name": "Петр"
    })
    assert booking2.status_code == 201
    
    # Шаг 2: Получаем расписание
    response = client.get(f"/rooms/{room_id}/bookings?date={date_str}")
    assert response.status_code == 200
    bookings = response.json()
    
    # Шаг 3: Проверяем результат
    assert len(bookings) == 2
    user_names = [b["user_name"] for b in bookings]
    assert "Иван" in user_names
    assert "Петр" in user_names