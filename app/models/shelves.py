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
from app.schemas import persons as person_schemas
from app.schemas import shelves as shelves_schemas
from typing import TYPE_CHECKING
from datetime import datetime, timedelta
import random
from app.models import Products

if TYPE_CHECKING:
    from app.models import Maps

class Shelves(Base):
    __tablename__ = "shelves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    map_id: Mapped[int] = mapped_column(Integer, ForeignKey("maps.id"), index=True)
    category: Mapped[str] = mapped_column(String)
    color_hex: Mapped[str] = mapped_column(String)
    capacity: Mapped[int] = mapped_column(Integer)
    x: Mapped[float] = mapped_column(Float)
    z: Mapped[float] = mapped_column(Float)

    map: Mapped["Maps"] = relationship("Maps", back_populates="shelves")
    products: Mapped[List["Products"]] = relationship("Products", back_populates="shelf")
    
    @staticmethod
    async def create(session, shelf_data: shelves_schemas.ShelfCreate):
        shelf = Shelves(**shelf_data.dict())
        session.add(shelf)
        await session.commit()
        return shelf

    @staticmethod
    async def get_by_id(session: AsyncSession, shelf_id: int) -> "Shelves":
        stmt = (
            select(Shelves)
            .where(Shelves.id == shelf_id)
            .options(selectinload(Shelves.products))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

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
