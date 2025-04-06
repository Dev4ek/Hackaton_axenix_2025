from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr
from app.schemas import categories as categories_schemas


from app.schemas import shelves as shelves_schemas
from app.schemas import kasses as kasses_schemas

class CategoryesOutput(BaseModel):
    id: int
    name: str
    products: list
                
          
class CreateCategoryProduct(BaseModel):
    name: str
    product_add: str    
    