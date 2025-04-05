from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


from app.schemas import shelves as shelves_schemas


class KassesBase(BaseModel):
    name: str = Field(
        ...,
        title="Имя кассы",
        example="Касса 1",
        max_length=100
    )    
    map_id: int = Field(
        ...,
        title="Идентификатор карты",
        example=1
    )
    x: int = Field(
        ...,
        title="Координата X",
        example=20,
    )
    z: int = Field(
        ...,
        title="Координата Z",
        example=15,
    )
    
    
class KassesCreate(KassesBase):
    pass

class KassesOutput(KassesBase):
    id: int
    created_at: datetime = Field(
        ...,
        title="Дата создания",
        example=datetime(2022, 1, 1, 12, 0, 0),
        description="Дата создания кассы",
    )