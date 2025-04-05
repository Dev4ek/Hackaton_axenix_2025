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

    

class PersonOutput(BaseModel):
    id: int
    map_id: int
    target_product: Optional[str] = Field(None)
    preferences: Optional[List[str]] = Field([])
    history_coordinates: Optional[List[str]] = Field([])
    created_at: datetime = Field(default_factory=datetime.now)
    
    