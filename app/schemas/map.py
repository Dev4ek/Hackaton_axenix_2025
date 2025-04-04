from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr

class MapCreate(BaseModel):
    name: str = Field(
        ...,
        title="Имя карты",
        example="Пятерочка"
    )

class MapOutput(BaseModel):
    id: int
    name: str
    created_at: datetime