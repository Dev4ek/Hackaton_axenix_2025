from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr

class SimulationCreate(BaseModel):
    map_id: int = Field(
        ...,
        title="Идентификатор карты",
        example=1,
    )
    num_persons: int = Field(
        ...,
        title="Количество человек",
        example=50,
    )
    
    