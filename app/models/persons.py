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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default='now()')    

    map: Mapped['Maps'] = relationship('Maps', back_populates='persons', uselist=False)
    movements: Mapped[List["PersonMovements"]] = relationship(
        "PersonMovements", 
        back_populates="person", 
        cascade="all, delete-orphan"
    )
    sales = relationship("Sales", back_populates="person")
    @staticmethod
    async def create(session: AsyncSession, payload: person_schemas.PersonCreate) -> "Persons":
        new_person = Persons(**payload.dict())
        products = await Products.get_all(session)
        if products != []:
            if random.random() > 0.5:
                rand_products = random.choice(products)
                new_person.target_product = rand_products.name
            else:
                new_person.target_product = None
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


class PersonMovements(Base):
    __tablename__ = "person_movements"
    
    id: Mapped[int] = mapped_column(Integer, autoincrement=True, index=True, primary_key=True)
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("persons.id"))
    map_id: Mapped[int] = mapped_column(Integer, ForeignKey("maps.id"))
    x: Mapped[int] = mapped_column(Integer)
    y: Mapped[int] = mapped_column(Integer)
    z: Mapped[int] = mapped_column(Integer)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default='now()')    

    person = relationship("Persons", back_populates="movements")
    map = relationship("Maps", back_populates="movements")
    
    @staticmethod
    async def get_by_map_id(session: AsyncSession, map_id: int):
        stmt = (
            select(PersonMovements)
           .where(PersonMovements.map_id == map_id)
        )
        result = await session.execute(stmt)
        return result.scalars().all()


class Sales(Base):
    __tablename__ = "sales"
    
    id: Mapped[int] = mapped_column(Integer, autoincrement=True, index=True, primary_key=True)
    person_id: Mapped[int] = mapped_column(Integer, ForeignKey("persons.id"))
    map_id: Mapped[int] = mapped_column(Integer, ForeignKey("maps.id"))
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"))
    
    price: Mapped[float] = mapped_column(Float, default=0.0, server_default='0.0')

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default='now()')    

    product = relationship("Products", back_populates="sales")
    map = relationship("Maps", back_populates="sales")
    person = relationship("Persons", back_populates="sales")
    @staticmethod
    async def get_total_sales(session: AsyncSession, map_id: int) -> int:
        stmt = (
            select(func.count(Sales.id))
            .where(Sales.map_id == map_id)
        )
        result = await session.execute(stmt)
        return result.scalar()  # or result.first()[0]

    @staticmethod
    async def get_total_revenue(session: AsyncSession, map_id: int) -> float:
        stmt = (
            select(func.sum(Sales.price))
            .where(Sales.map_id == map_id)
        )
        result = await session.execute(stmt)
        return result.scalar() or 0.0

    @staticmethod
    async def get_sales_grouped_by_product(session: AsyncSession, map_id: int):
        """
        Возвращает список словарей, где по каждому product_id
        указаны общий счётчик продаж и суммарная выручка.
        """
        # Используем select(...) вместо session.query(...) для асинхронного стиля
        stmt = (
            select(
                Sales.product_id,
                func.count(Sales.id).label("count_sold"),
                func.sum(Sales.price).label("revenue")
            )
            .where(Sales.map_id == map_id)
            .group_by(Sales.product_id)
        )

        # Выполняем запрос
        result = await session.execute(stmt)
        rows = result.all()  # Список Row-объектов

        # Преобразуем строки в удобный формат
        # Предположим, каждая row будет вида (product_id, count_sold, revenue)
        # либо Row(product_id=..., count_sold=..., revenue=...)
        grouped = []
        for row in rows:
            # Если row — это Row-объект, можно обращаться через row.product_id (или row[0], в зависимости от версии SQLAlchemy)
            grouped.append({
                "product_id": row.product_id,
                "count_sold": row.count_sold,
                "revenue": float(row.revenue or 0)
            })

        return grouped
    
    @staticmethod
    async def get_discount_effectiveness(session: AsyncSession, map_id: int, base_price: float = 100.0):
        """
        Возвращает словарь с данными о количестве продаж 
        со скидкой (price < base_price) и доле таких продаж.
        
        :param session: AsyncSession
        :param map_id: id карты (магазина)
        :param base_price: базовая цена (упрощённо 100)
        """
        # Сколько продаж было сделано дешевле, чем base_price (т. е. со скидкой)
        discounted_stmt = (
            select(func.count(Sales.id))
            .where(Sales.map_id == map_id)
            .where(Sales.price < base_price)
        )
        discounted_result = await session.execute(discounted_stmt)
        discounted_sales = discounted_result.scalar() or 0

        # Общее количество продаж
        total_stmt = (
            select(func.count(Sales.id))
            .where(Sales.map_id == map_id)
        )
        total_result = await session.execute(total_stmt)
        total_sales = total_result.scalar() or 0

        if total_sales == 0:
            return {
                "discounted_sales": 0,
                "total_sales": 0,
                "discount_ratio": 0
            }

        ratio = discounted_sales / total_sales

        return {
            "discounted_sales": discounted_sales,
            "total_sales": total_sales,
            "discount_ratio": ratio
        }