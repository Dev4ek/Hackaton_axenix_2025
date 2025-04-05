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
    

class MapOutput(BaseModel):
    id: int
    name: str
    x: int
    z: int
    created_at: datetime