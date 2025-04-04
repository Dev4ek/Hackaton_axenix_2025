from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr

class PersonCreate(BaseModel):
    x: int = Field(
       ...,
        title="Координата X",
        example=20
    )
    y: int = Field(
        ...,
        title="Координата Y",
        example=30
    )
    z: int = Field(
        ...,
        title="Координата Z",
        example=40
    )
    preferences: Optional[List[str]] = Field(
        None,
        title="Предпочтения",
        example=["Молоко", "Хлеб"]
    )
    history_coordinates: Optional[List[str]] = Field(
        None,
        title="История кординат",
        example=["1, 2, 5.4, 5032"]
    )
    
   
    
    
    

class PersoOutput(BaseModel):
    