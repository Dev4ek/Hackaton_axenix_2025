from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr

class PersonCreate(BaseModel):
    map_id: int = Field(
        ...,
        title="Идентификатор карты",
        example=1,
    )
    preferences: Optional[List[str]] = Field(
        [],
        title="Предпочтения",
        example=["Молоко", "Хлеб"]
    )
    history_coordinates: Optional[List[str]] = Field(
        None,
        title="История кординат",
        example=["1, 2, 5.4, 5032"]
    )
    
   
    
    
    

class PersoOutput(BaseModel):
    