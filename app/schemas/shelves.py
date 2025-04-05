from pydantic import BaseModel
from typing import Optional

class ShelfBase(BaseModel):
    map_id: int
    name: str
    x: float
    y: float
    z: float
    capacity: int

class ShelfCreate(ShelfBase):
    pass

class ShelfOutput(ShelfBase):
    id: int

