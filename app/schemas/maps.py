from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr

from app.schemas.persons import PersonOutput
from app.schemas.products import ProductOutput

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
    
    time_peak_start: int = Field(
        ...,
        title="Время начала пиковой часовой смены",
        example=54421,
    )
    time_peak_end: int = Field(
        ...,
        title="Время окончания пиковой часовой смены",
        example=77534,
    )   
   
    

class MapOutput(BaseModel):
    id: int
    name: str
    x: int
    z: int
    time_peak_start: int
    time_peak_end: int
    created_at: datetime
    
class MapFullOutput(BaseModel):
    id: int
    name: str
    x: int
    z: int
    time_peak_start: int
    time_peak_end: int
    created_at: datetime
    persons: Optional[List[PersonOutput]] = None
    products: Optional[List[ProductOutput]] = None
    
    
