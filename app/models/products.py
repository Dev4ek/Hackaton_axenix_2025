import random
from typing import List, Optional
from sqlalchemy import (
    ARRAY,
    Float,
    ForeignKey,
    String,
    Integer,
    Boolean,
    Numeric,
    BigInteger,
    Sequence,
    and_,
    func,
    or_,
    select,
    text,
    update,
    DateTime,
    UUID as PostgresUUID,
    or_,
    JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload
from app.base import Base
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TYPE_CHECKING
from datetime import datetime, timedelta
from app.schemas import products as products_schemas
from sqlalchemy.dialects.postgresql import JSONB

if TYPE_CHECKING:
    from app.models import Maps, Shelves, Sales

class Products(Base):
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(Integer, autoincrement=True, index=True, primary_key=True)
    shelf_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("shelves.id"), nullable=True)

    name: Mapped[str] = mapped_column(String(100))
    color_hex: Mapped[str] = mapped_column(String(255), nullable=True)
    
    time_discount_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    time_discount_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    percent_discount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    shelf: Mapped["Shelves"] = relationship("Shelves", back_populates="products")
    sales: Mapped["Sales"] = relationship("Sales", back_populates="product")
    
    @staticmethod
    async def create(session: AsyncSession, payload: products_schemas.ProductCreate) -> "Products":
        new_product = Products(**payload.dict())
        session.add(new_product)
        await session.commit()
        return new_product
    
    @staticmethod
    async def get_by_id(session: AsyncSession, product_id: int) -> Optional["Products"]:
        _product = await session.get(Products, product_id) 
        return _product
    
    @staticmethod
    async def get_all(session: AsyncSession, offset: int = 0, limit: int = 10) -> List["Products"]:
        stmt = (
            select(Products)
           .offset(offset)
           .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_by_map_id(session: AsyncSession, map_id: int) -> List["Products"]:
        stmt = (
            select(Products)
           .where(Products.map_id == map_id)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    