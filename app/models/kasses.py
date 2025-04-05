import random
from typing import List, Optional
from sqlalchemy import (
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
from app.schemas import maps as main_schemas
from app.schemas import kasses as kasses_schemas
from typing import TYPE_CHECKING
from datetime import datetime, timedelta

if TYPE_CHECKING:
    from app.models import Maps

class Kasses(Base):
    __tablename__ = "kasses"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, index=True, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    map_id: Mapped[int] = mapped_column(Integer, ForeignKey("maps.id"), index=True)
    x: Mapped[int] = mapped_column(Integer)
    z: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default='now()')    
    
    map: Mapped["Maps"] = relationship("Maps", back_populates="kassses")
  
    @staticmethod
    async def create(session: AsyncSession, kasse_data: kasses_schemas.KassesCreate) -> "Kasses":
        kasses = Kasses(**kasse_data.dict())
        session.add(kasses)
        await session.commit()
        return kasses
    
    @staticmethod
    async def get_all(session: AsyncSession, offset: int = 0, limit: int = 10) -> List['Kasses']:
        stmt = (
            select(Kasses)
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_by_id(session: AsyncSession, kasse_id: int) -> Optional['Kasses']:
        return await session.get(Kasses, kasse_id)
    
    @staticmethod
    async def get_by_map_id(session: AsyncSession, map_id: int) -> List['Kasses']:
        stmt = (
            select(Kasses)
            .where(Kasses.map_id == map_id)
        )
        result = await session.execute(stmt)
        return result.scalars().all()