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

class Persons(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(Integer, autoincrement=True, index=True, primary_key=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"))
                                            
    preferences: Mapped[List[str]] = mapped_column(JSON)
    history_coordinates: Mapped[List[str]] = mapped_column(JSON)

    product: Mapped['Products'] = relationship('Products', back_populates='persons', uselist=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default='now()')    
    