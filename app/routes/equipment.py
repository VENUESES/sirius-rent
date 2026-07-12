from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from ..database import get_db
from ..repositories.equipment_repository import EquipmentRepository
from ..schemas import EquipmentCreate, Equipment

router = APIRouter(prefix="/equipment", tags=["Оборудование"])

# === ПОЛУЧИТЬ ВСЁ ОБОРУДОВАНИЕ ===
@router.get("/", response_model=List[Equipment])
def get_equipment(
    skip: int = Query(0, ge=0, description="Смещение"),
    limit: int = Query(100, ge=1, le=100, description="Лимит"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    search: Optional[str] = Query(None, description="Поиск по названию"),
    db: Session = Depends(get_db)
):
    """
    Получить список всего оборудования с возможностью фильтрации.
    """
    repo = EquipmentRepository(db)
    
    # Если есть категория
    if category:
        return repo.get_by_category(category)
    
    # Если есть поиск
    if search:
        all_equipment = repo.get_multi(skip=skip, limit=limit)
        return [e for e in all_equipment if search.lower() in e.name.lower()]
    
    return repo.get_multi(skip=skip, limit=limit)

# === СОЗДАТЬ ОБОРУДОВАНИЕ ===
@router.post("/", response_model=Equipment, status_code=201)
def create_equipment(
    equipment: EquipmentCreate,
    db: Session = Depends(get_db)
):
    """
    Создать новое оборудование.
    """
    repo = EquipmentRepository(db)
    
    # Проверяем, не существует ли уже
    existing = repo.get_by_name(equipment.name)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Equipment '{equipment.name}' already exists"
        )
    
    return repo.create(equipment)

# === ПОЛУЧИТЬ ОБОРУДОВАНИЕ ПО ID ===
@router.get("/{equipment_id}", response_model=Equipment)
def get_equipment_by_id(
    equipment_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить детальную информацию об оборудовании.
    """
    repo = EquipmentRepository(db)
    equipment = repo.get(equipment_id)
    
    if not equipment:
        raise HTTPException(
            status_code=404,
            detail=f"Equipment with id {equipment_id} not found"
        )
    
    return equipment

# === ОБНОВИТЬ ОБОРУДОВАНИЕ ===
@router.put("/{equipment_id}", response_model=Equipment)
def update_equipment(
    equipment_id: int,
    equipment: EquipmentCreate,
    db: Session = Depends(get_db)
):
    """
    Обновить данные об оборудовании.
    """
    repo = EquipmentRepository(db)
    
    # Проверяем, существует ли
    existing = repo.get(equipment_id)
    if not existing:
        raise HTTPException(
            status_code=404,
            detail=f"Equipment with id {equipment_id} not found"
        )
    
    # Проверяем, не занято ли новое название
    if equipment.name != existing.name:
        name_exists = repo.get_by_name(equipment.name)
        if name_exists:
            raise HTTPException(
                status_code=409,
                detail=f"Equipment '{equipment.name}' already exists"
            )
    
    updated = repo.update(equipment_id, equipment)
    return updated

# === УДАЛИТЬ ОБОРУДОВАНИЕ ===
@router.delete("/{equipment_id}", status_code=204)
def delete_equipment(
    equipment_id: int,
    db: Session = Depends(get_db)
):
    """
    Удалить оборудование.
    """
    repo = EquipmentRepository(db)
    
    # Проверяем, используется ли в комнатах
    equipment = repo.get(equipment_id)
    if not equipment:
        raise HTTPException(
            status_code=404,
            detail=f"Equipment with id {equipment_id} not found"
        )
    
    # Проверяем, используется ли оборудование
    rooms_with_equipment = repo.get_rooms_with_equipment(equipment_id)
    if rooms_with_equipment:
        room_names = [r.name for r in rooms_with_equipment]
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Equipment is used in rooms",
                "rooms": room_names
            }
        )
    
    repo.delete(equipment_id)

# === ПОПУЛЯРНОЕ ОБОРУДОВАНИЕ ===
@router.get("/popular", response_model=List[dict])
def get_popular_equipment(
    limit: int = Query(10, ge=1, le=50, description="Количество"),
    db: Session = Depends(get_db)
):
    """
    Получить самое популярное оборудование 
    (по количеству комнат, где оно используется).
    """
    repo = EquipmentRepository(db)
    return repo.get_most_popular(limit)