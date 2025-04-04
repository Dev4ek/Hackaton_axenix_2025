from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr

class MapCreate(BaseModel):
    name: str = Field(
        ...,
        title="Имя карты",
        example="Пятерочка",
        max_length=100
    )
    map_id: int = Field(
        ...,
        title="Идентификатор карты",
        example=4
    )
    x: int = Field(
        ...,
        title="Координата X",
        example=20
    )
    z: int = Field(
        ...,
        title="Координата Z",
        example=15
    )
    
    
    

class MapOutput(BaseModel):
    id: int
    name: str
    map_id: int
    x: int
    z: int
    created_at: datetime