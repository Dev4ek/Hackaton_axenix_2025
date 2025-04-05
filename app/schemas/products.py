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
    map_id: int = Field(
        ...,
        title="Идентификатор карты",
        example=4
    )
    
    color_hex: str = Field(
        ...,
        title="Цвет продукта в HEX формате",
        example="#FF0000",
    )
    x: float = Field(
        ...,
        title="Координата X",
        example=50.5,
    )
    y: float = Field(
        ...,
        title="Координата Y",
        example=50.5,
    )
    z: float = Field(
        ...,
        title="Координата Z",
        example=50.5,
    )
    
    
class ProductOutput(BaseModel):
    id: int
    name: str
    color_hex: Optional[str] = None
    x: float
    y: float
    z: float
   
