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
import random
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload
from app.base import Base
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import persons as person_schemas
from typing import TYPE_CHECKING
from datetime import datetime, timedelta
from products import Products
from app.dependencies import SessionDep

if TYPE_CHECKING:
    from app.models import Maps

class Persons(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, index=True, primary_key=True)
    map_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"))
    # target_product: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    target_product: Mapped[Optional[str]] = random.choice(Products.get_all(SessionDep))

    preferences: Mapped[List[str]] = mapped_column(JSON) # Пример: ['Любит скидки']
    history_coordinates: Mapped[List[str]] = mapped_column(JSON) # Пример: ['x', 'y', 'z', 'время']
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default='now()')    

    map: Mapped['Maps'] = relationship('Maps', back_populates='persons', uselist=False)
    
    @staticmethod
    async def create(session: AsyncSession, payload: person_schemas.PersonCreate) -> "Persons":
        new_person = Persons(**payload.dict())
        session.add(new_person)
        await session.commit()
        return new_person
    
    @staticmethod
    async def get_by_id(session: AsyncSession, person_id: int) -> Optional["Persons"]:
        _person = await session.get(Persons, person_id) 
        return _person
    
    @staticmethod
    async def get_all(session: AsyncSession, offset: int = 0, limit: int = 10) -> List["Persons"]:
        stmt = (
            select(Persons)
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_by_map_id(session: AsyncSession, map_id: int) -> List["Persons"]:
        stmt = (
            select(Persons)
           .where(Persons.map_id == map_id)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
