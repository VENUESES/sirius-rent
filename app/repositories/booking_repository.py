from typing import Optional, List
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models import Booking, Room, BookingStatus
from ..schemas import BookingCreate
from ..repositories.base import BaseRepository

class BookingRepository(BaseRepository[Booking, BookingCreate, BookingCreate]):
    
    def __init__(self, db: Session):
        super().__init__(Booking, db)
    
    def get_by_room_and_date(self, room_id: int, booking_date: date) -> List[Booking]:
        start = datetime.combine(booking_date, datetime.min.time())
        end = datetime.combine(booking_date, datetime.max.time())
        
        return self.db.query(Booking).filter(
            and_(
                Booking.room_id == room_id,
                Booking.start_time >= start,
                Booking.start_time <= end,
                Booking.status == BookingStatus.ACTIVE
            )
        ).order_by(Booking.start_time).all()
    
    def check_availability(self, room_id: int, start_time: datetime, end_time: datetime) -> bool:
        conflict = self.db.query(Booking).filter(
            and_(
                Booking.room_id == room_id,
                Booking.status == BookingStatus.ACTIVE,
                Booking.start_time < end_time,
                Booking.end_time > start_time
            )
        ).first()
        return conflict is None
    
    def create_with_check(self, booking_data: BookingCreate) -> Optional[Booking]:
        room = self.db.query(Room).filter(Room.id == booking_data.room_id).first()
        if not room:
            raise ValueError("Room not found")
        
        if not self.check_availability(
            booking_data.room_id,
            booking_data.start_time,
            booking_data.end_time
        ):
            return None
        
        booking = Booking(**booking_data.model_dump())
        self.db.add(booking)
        self.db.commit()
        self.db.refresh(booking)
        return booking
    
    def cancel(self, booking_id: int) -> Optional[Booking]:
        booking = self.get(booking_id)
        if not booking:
            return None
        
        booking.status = BookingStatus.CANCELLED
        self.db.commit()
        self.db.refresh(booking)
        return booking