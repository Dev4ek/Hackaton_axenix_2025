from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr

class ProductCreate(BaseModel):
    name: str = Field(
        ...,
        title="Имя продукта",
        example="Молоко",
        max_length=100
    )
    x: float = Field(
        ...,
        title="Координата X",
        example=50.5,
        gt=0
    )
    y: float = Field(
        ...,
        title="Координата Y",
        example=50.5,
        gt=0
    )
    z: float = Field(
        ...,
        title="Координата Z",
        example=50.5,
        gt=0
    )
    
    
class ProductOutput(BaseModel):
    id: int
    name: str
    x: float
    y: float
    z: float
    