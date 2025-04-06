import random
from typing import List, Optional
from sqlalchemy import (
    ARRAY,
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
from app.models import Products, Persons, Shelves, Kasses
from app.schemas import maps as main_schemas
from typing import TYPE_CHECKING
from datetime import datetime, timedelta


class Categories(Base):
    __tablename__ = "categories"
    
    id: Mapped[int] = mapped_column(Integer, autoincrement=True, index=True, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    products: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)

    @staticmethod  
    async def get_all(session: AsyncSession) -> List['Categories']:
        stmt = (
            select(Categories)
            .order_by(Categories.name)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
        
    @staticmethod
    async def get_by_name(session: AsyncSession, name: str) -> Optional['Categories']:
        stmt = (
            select(Categories)
            .where(Categories.name == name)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    