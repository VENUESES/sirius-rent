from typing import Optional, List
from sqlalchemy.orm import Session
from ..models import Equipment
from ..schemas import EquipmentCreate
from ..repositories.base import BaseRepository

class EquipmentRepository(BaseRepository[Equipment, EquipmentCreate, EquipmentCreate]):
    
    def __init__(self, db: Session):
        super().__init__(Equipment, db)
    
    def get_by_name(self, name: str) -> Optional[Equipment]:
        return self.db.query(Equipment).filter(Equipment.name == name).first()