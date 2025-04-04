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
from app.schemas import persons as person_schemas
from typing import TYPE_CHECKING
from datetime import datetime, timedelta
import random
from app.models import Products

if TYPE_CHECKING:
    from app.models import Maps

class Persons(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, index=True, primary_key=True)
    map_id: Mapped[int] = mapped_column(Integer, ForeignKey("maps.id"))
    target_product: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    preferences: Mapped[List[str]] = mapped_column(JSON, default=[], server_default='[]') # Пример: ['Любит скидки']
    history_coordinates: Mapped[List[str]] = mapped_column(JSON, default=[], server_default='[]') # Пример: ['x', 'y', 'z', 'время']
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default='now()')    

    map: Mapped['Maps'] = relationship('Maps', back_populates='persons', uselist=False)
    
    @staticmethod
    async def create(session: AsyncSession, payload: person_schemas.PersonCreate) -> "Persons":
        new_person = Persons(**payload.dict())
        products = await Products.get_all(session)
        if products != []:
            rand_products = random.choice(products)
            new_person.target_product = rand_products.name
        else:
            new_person.target_product = None
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
