from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from ..database import get_db
from ..repositories.booking_repository import BookingRepository
from ..repositories.room_repository import RoomRepository
from ..schemas import BookingCreate, Booking, BookingWithRoom

router = APIRouter(prefix="/bookings", tags=["Бронирования"])

# === СОЗДАТЬ БРОНИРОВАНИЕ ===
@router.post("/", response_model=Booking, status_code=201)
def create_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db)
):
    """
    Создать новое бронирование с проверкой доступности комнаты.
    Если комната занята - вернёт ошибку 409 Conflict.
    """
    repo = BookingRepository(db)
    room_repo = RoomRepository(db)
    
    # Проверяем, существует ли комната
    room = room_repo.get(booking.room_id)
    if not room:
        raise HTTPException(
            status_code=404,
            detail=f"Room with id {booking.room_id} not found"
        )
    
    # Проверяем доступность
    if not repo.check_availability(booking.room_id, booking.start_time, booking.end_time):
        # Получаем конфликтующие бронирования для детального ответа
        conflicts = repo.get_conflicting_bookings(
            booking.room_id,
            booking.start_time,
            booking.end_time
        )
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Room is already booked for the selected time",
                "conflicts": [
                    {
                        "id": b.id,
                        "start_time": b.start_time.isoformat(),
                        "end_time": b.end_time.isoformat(),
                        "user_name": b.user_name
                    }
                    for b in conflicts
                ]
            }
        )
    
    try:
        new_booking = repo.create_with_check(booking)
        if not new_booking:
            raise HTTPException(
                status_code=409,
                detail="Room is already booked for the selected time"
            )
        return new_booking
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# === ПОЛУЧИТЬ БРОНИРОВАНИЯ КОМНАТЫ НА ДЕНЬ ===
@router.get("/rooms/{room_id}/bookings", response_model=List[Booking])
def get_room_bookings(
    room_id: int,
    date: date = Query(..., description="Дата в формате YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    Получить все активные бронирования для конкретной комнаты на выбранную дату.
    """
    repo = BookingRepository(db)
    room_repo = RoomRepository(db)
    
    # Проверяем, существует ли комната
    room = room_repo.get(room_id)
    if not room:
        raise HTTPException(
            status_code=404,
            detail=f"Room with id {room_id} not found"
        )
    
    return repo.get_by_room_and_date(room_id, date)

# === ОТМЕНИТЬ БРОНИРОВАНИЕ ===
@router.delete("/{booking_id}", response_model=Booking)
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db)
):
    """
    Отменить бронирование по ID.
    Статус меняется на "отменено".
    """
    repo = BookingRepository(db)
    
    booking = repo.cancel(booking_id)
    if not booking:
        raise HTTPException(
            status_code=404,
            detail=f"Booking with id {booking_id} not found"
        )
    
    return booking

# === ПОЛУЧИТЬ ВСЕ БРОНИРОВАНИЯ (для администрирования) ===
@router.get("/", response_model=List[Booking])
def get_all_bookings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    user_name: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Получить список всех бронирований с фильтрацией.
    """
    repo = BookingRepository(db)
    
    if user_name:
        from app.models import BookingStatus
        status_enum = None
        if status:
            try:
                status_enum = BookingStatus(status)
            except ValueError:
                pass
        return repo.get_user_bookings(user_name, status_enum)
    
    if status:
        from app.models import BookingStatus
        try:
            status_enum = BookingStatus(status)
            return repo.get_multi(skip=skip, limit=limit, filters={"status": status_enum})
        except ValueError:
            pass
    
    return repo.get_multi(skip=skip, limit=limit)

# === ПОЛУЧИТЬ БРОНИРОВАНИЕ ПО ID ===
@router.get("/{booking_id}", response_model=BookingWithRoom)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить детальную информацию о бронировании.
    """
    repo = BookingRepository(db)
    booking = repo.get(booking_id)
    
    if not booking:
        raise HTTPException(
            status_code=404,
            detail=f"Booking with id {booking_id} not found"
        )
    
    return booking
