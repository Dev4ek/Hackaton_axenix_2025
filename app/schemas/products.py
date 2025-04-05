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
    
    percent_discount: Optional[int] = Field(
        None,
        title="Процент скидки",
        example=3,
    )
    time_discount_start: Optional[int] = Field(
        None,
        title="Время начала скидки",
        example=32412,
    )
    time_discount_end: Optional[int] = Field(
        None,
        title="Время конца скидки",
        example=48542,
    )
    
    
class ProductOutput(BaseModel):
    id: int
    name: str
    color_hex: Optional[str] = None
    x: float
    y: float
    z: float
    percent_discount: Optional[int] = None
    time_discount_start: Optional[int] = None
    time_discount_end: Optional[int] = None
   
