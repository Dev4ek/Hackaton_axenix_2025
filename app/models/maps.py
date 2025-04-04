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
from typing import TYPE_CHECKING
from datetime import datetime, timedelta

if TYPE_CHECKING:
    from app.models import Products

class Maps(Base):
    __tablename__ = "maps"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, index=True, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    x: Mapped[int] = mapped_column(Integer)
    z: Mapped[int] = mapped_column(Integer)

    products: Mapped[List['Products']] = relationship('Products', back_populates='map')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default='now()')    
    
    @staticmethod
    async def create(session: AsyncSession, payload: main_schemas.MapCreate) -> "Maps":
        new_map = Maps(**payload.dict())
        session.add(new_map)
        await session.commit()
        return new_map
    
    @staticmethod
    async def get_by_id(session: AsyncSession, map_id: int) -> Optional["Maps"]:
        _map = await session.get(Maps, map_id) 
        return _map
    
    @staticmethod
    async def get_all(session: AsyncSession, offset: int = 0, limit: int = 10) -> List["Maps"]:
        stmt = (
            select(Maps)
            .order_by(Maps.created_at.desc())
            .offset(offset)
        )
        result = await session.execute(stmt)
        return result.scalars().all()