from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


from app.schemas import shelves as shelves_schemas


class MapBase(BaseModel):
    name: str = Field(
        ...,
        title="Имя карты",
        example="Пятерочка",
        max_length=100
    )
    x: int = Field(
        ...,
        title="Координата X",
        example=20,
        ge=0
    )
    z: int = Field(
        ...,
        title="Координата Z",
        example=15,
        ge=0
    )
    
class MapCreate(MapBase):
    pass

class MapOutput(MapBase):
    id: int
    created_at: datetime

class MapShelves(MapBase):
    shelves: List[shelves_schemas.ShelfProducts] = Field(
        [],
        title="Стелажи",
    )


    