import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import Room, Equipment, room_equipment

# ============================================
# НАСТРОЙКА ТЕСТОВОЙ БАЗЫ ДАННЫХ
# ============================================

# Создаём тестовую БД в памяти
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Переопределяем зависимость get_db для тестов
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Создаём клиент для тестирования
client = TestClient(app)

# ============================================
# ФИКСТУРЫ
# ============================================

@pytest.fixture(autouse=True)
def setup_db():
    """Создаём таблицы перед каждым тестом и удаляем после"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_equipment():
    """Создаём тестовое оборудование"""
    response = client.post("/equipment/", json={
        "name": "проектор",
        "description": "Full HD проектор для тестов"
    })
    return response.json()

@pytest.fixture
def test_room(test_equipment):
    """Создаём тестовую комнату с оборудованием"""
    response = client.post("/rooms/", json={
        "name": "Тестовая комната",
        "capacity": 20,
        "description": "Комната для тестирования",
        "equipment": [
            {
                "equipment_id": test_equipment["id"],
                "count": 2,
                "condition": "исправно"
            }
        ]
    })
    return response.json()

# ============================================
# ТЕСТ 1: СОЗДАНИЕ КОМНАТЫ
# ============================================

def test_create_room():
    """Тест создания комнаты с оборудованием"""
    # Шаг 1: Создаём оборудование
    eq_response = client.post("/equipment/", json={
        "name": "тестовый-проектор",
        "description": "Для теста"
    })
    assert eq_response.status_code == 201
    eq_data = eq_response.json()
    assert eq_data["name"] == "тестовый-проектор"
    
    # Шаг 2: Создаём комнату с этим оборудованием
    room_response = client.post("/rooms/", json={
        "name": "Новая комната",
        "capacity": 15,
        "description": "Создана в тесте",
        "equipment": [
            {
                "equipment_id": eq_data["id"],
                "count": 1,
                "condition": "исправно"
            }
        ]
    })
    assert room_response.status_code == 201
    room_data = room_response.json()
    
    # Шаг 3: Проверяем результат
    assert room_data["name"] == "Новая комната"
    assert room_data["capacity"] == 15
    assert room_data["description"] == "Создана в тесте"
    assert len(room_data["equipment"]) == 1
    assert room_data["equipment"][0]["name"] == "тестовый-проектор"

# ============================================
# ТЕСТ 2: ПОЛУЧЕНИЕ СПИСКА КОМНАТ
# ============================================

def test_get_rooms():
    """Тест получения списка комнат"""
    # Шаг 1: Создаём оборудование
    eq_response = client.post("/equipment/", json={
        "name": "проектор-для-списка",
        "description": "Для теста списка"
    })
    assert eq_response.status_code == 201
    eq_id = eq_response.json()["id"]
    
    # Шаг 2: Создаём несколько комнат
    room1 = client.post("/rooms/", json={
        "name": "Комната А",
        "capacity": 10,
        "equipment": [{"equipment_id": eq_id, "count": 1, "condition": "исправно"}]
    })
    assert room1.status_code == 201
    
    room2 = client.post("/rooms/", json={
        "name": "Комната Б",
        "capacity": 20,
        "equipment": []
    })
    assert room2.status_code == 201
    
    # Шаг 3: Получаем список комнат
    response = client.get("/rooms/")
    assert response.status_code == 200
    rooms = response.json()
    
    # Шаг 4: Проверяем результат
    assert len(rooms) >= 2
    names = [room["name"] for room in rooms]
    assert "Комната А" in names
    assert "Комната Б" in names

# ============================================
# ТЕСТ 3: ПОЛУЧЕНИЕ КОМНАТЫ ПО ID
# ============================================

def test_get_room_by_id(test_room):
    """Тест получения комнаты по ID"""
    room_id = test_room["id"]
    
    response = client.get(f"/rooms/{room_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == room_id
    assert data["name"] == "Тестовая комната"
    assert data["capacity"] == 20
    assert len(data["equipment"]) == 1

# ============================================
# ТЕСТ 4: ПОИСК КОМНАТ ПО ВМЕСТИМОСТИ
# ============================================

def test_get_rooms_by_capacity():
    """Тест фильтрации комнат по вместимости"""
    # Создаём оборудование
    eq_response = client.post("/equipment/", json={
        "name": "проектор-для-фильтра",
        "description": "Для теста фильтрации"
    })
    assert eq_response.status_code == 201
    eq_id = eq_response.json()["id"]
    
    # Создаём комнаты с разной вместимостью
    client.post("/rooms/", json={
        "name": "Малая комната",
        "capacity": 5,
        "equipment": [{"equipment_id": eq_id, "count": 1, "condition": "исправно"}]
    })
    client.post("/rooms/", json={
        "name": "Большая комната",
        "capacity": 20,
        "equipment": [{"equipment_id": eq_id, "count": 1, "condition": "исправно"}]
    })
    
    # Фильтр: capacity >= 10
    response = client.get("/rooms/?capacity=10")
    assert response.status_code == 200
    rooms = response.json()
    
    # Проверяем: все комнаты имеют capacity >= 10
    for room in rooms:
        assert room["capacity"] >= 10
    
    # Проверяем: большая комната есть, малой нет
    names = [room["name"] for room in rooms]
    assert "Большая комната" in names
    assert "Малая комната" not in names