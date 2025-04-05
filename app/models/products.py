import random
from typing import List, Optional
from sqlalchemy import (
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

if TYPE_CHECKING:
    from app.models import Maps


class Shelves(Base):
    __tablename__ = "shelves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    map_id: Mapped[int] = mapped_column(Integer, ForeignKey("maps.id"), index=True)
    
    name: Mapped[str] = mapped_column(String(100))
    x: Mapped[float] = mapped_column(Float)
    y: Mapped[float] = mapped_column(Float)
    z: Mapped[float] = mapped_column(Float)
    


    capacity: Mapped[int] = mapped_column(Integer, default=10)

    # Связь с Maps (один-to-многие: одна карта -> много стеллажей)
    map: Mapped["Maps"] = relationship("Maps", back_populates="shelves")

    products: Mapped[List["Products"]] = relationship("Products", back_populates="shelf")
    @staticmethod
    async def create(session, shelf_data):
        shelf = Shelves(**shelf_data.dict())
        session.add(shelf)
        await session.commit()
        return shelf

    @staticmethod
    async def get_by_id(session, shelf_id: int):
        return await session.get(Shelves, shelf_id)

    @staticmethod
    async def get_by_map_id(session, map_id: int):
        from sqlalchemy import select
        stmt = select(Shelves).where(Shelves.map_id == map_id)
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_all(session, offset=0, limit=10):
        from sqlalchemy import select
        stmt = select(Shelves).offset(offset).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def delete_shelf(session, shelf_id: int):
        shelf = await Shelves.get_by_id(session, shelf_id)
        if shelf:
            await session.delete(shelf)
            await session.commit()
        return shelf
    
    
class Products(Base):
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(Integer, autoincrement=True, index=True, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    map_id: Mapped[int] = mapped_column(Integer, ForeignKey("maps.id"))
    color_hex: Mapped[str] = mapped_column(String(255), nullable=True)
    x: Mapped[float] = mapped_column(Float)
    y: Mapped[float] = mapped_column(Float)
    z: Mapped[float] = mapped_column(Float)
    
    time_discount_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    time_discount_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    percent_discount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    shelf_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("shelves.id"), nullable=True)
    shelf: Mapped[Optional["Shelves"]] = relationship("Shelves", back_populates="products")
    
    map: Mapped['Maps'] = relationship('Maps', back_populates='products', uselist=False)
    sales = relationship("Sales", back_populates="product")
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
    