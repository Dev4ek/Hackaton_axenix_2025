from pydantic import BaseModel
from typing import Optional

class ShelfBase(BaseModel):
    name: str
    map_id: int
    category: str
    color_hex: str
    x: float
    y: float
    z: float

class ShelfCreate(ShelfBase):
    pass

class ShelfOutput(ShelfBase):
    id: int

