from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas import products as products_schemas

class ShelfBase(BaseModel):
    name: str
    map_id: int
    category: str
    color_hex: str
    capacity: int
    x: float
    z: float

class ShelfCreate(ShelfBase):
    pass

class ShelfOutput(ShelfBase):
    id: int
    
class ShelfProducts(ShelfOutput):
    products: Optional[List[products_schemas.ProductOutput]] = Field(
        [],
    )

