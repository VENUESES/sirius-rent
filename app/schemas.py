from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List

# === ОБОРУДОВАНИЕ ===
class EquipmentBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None

class EquipmentCreate(EquipmentBase):
    pass

class Equipment(EquipmentBase):
    id: int
    
    class Config:
        from_attributes = True

# === ОБОРУДОВАНИЕ В КОМНАТЕ ===
class RoomEquipmentBase(BaseModel):
    equipment_id: int = Field(gt=0)
    count: int = Field(default=1, ge=1)
    condition: str = Field(default="исправно", min_length=1)

class RoomEquipmentCreate(RoomEquipmentBase):
    pass

class RoomEquipment(RoomEquipmentBase):
    equipment: Equipment
    
    class Config:
        from_attributes = True

# === КОМНАТЫ ===
class RoomBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    capacity: int = Field(gt=0, le=1000)
    description: Optional[str] = None

class RoomCreate(RoomBase):
    equipment: List[RoomEquipmentCreate] = []

class RoomUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    capacity: Optional[int] = Field(None, gt=0, le=1000)
    description: Optional[str] = None
    equipment: Optional[List[RoomEquipmentCreate]] = None

class Room(RoomBase):
    id: int
    equipment: List[Equipment] = []
    
    class Config:
        from_attributes = True

class RoomWithDetails(Room):
    equipment_with_count: List[RoomEquipment] = []
    
    class Config:
        from_attributes = True

# === БРОНИРОВАНИЯ ===
class BookingBase(BaseModel):
    room_id: int = Field(gt=0)
    start_time: datetime
    end_time: datetime
    user_name: str = Field(min_length=2, max_length=100)

    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

class BookingCreate(BookingBase):
    pass

class Booking(BookingBase):
    id: int
    status: str
    
    class Config:
        from_attributes = True

# ⭐ БРОНИРОВАНИЕ С КОМНАТОЙ
class BookingWithRoom(Booking):
    """Бронирование с полной информацией о комнате"""
    room: Room
    
    class Config:
        from_attributes = True