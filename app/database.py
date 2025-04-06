import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker as sync_sessionmaker
from sqlalchemy import select, insert, create_engine

from .config import settings
from .base import Base
from contextlib import contextmanager
from contextlib import asynccontextmanager
from .base import Base


engine = create_async_engine(
    url=settings.SQLALCHEMY_DATABASE_URL,
    echo=False,  # Логирование SQL-запросов (True для отладки)
    pool_size=10,  # Размер пула соединений
    max_overflow=20,  # Дополнительные соединения при высокой нагрузке
    pool_timeout=30,  # Тайм-аут ожидания свободного соединения
    pool_recycle=1800,  # Рецикл соединений для предотвращения разрывов
    pool_pre_ping=True,  # Проверка соединений перед использованием
)

sessionmaker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

engine_sync = create_engine(url=settings.SQLALCHEMY_DATABASE_SYNC_URL)
SyncSession = sync_sessionmaker(bind=engine_sync, autocommit=False, autoflush=False,)

async def get_session():
    async with sessionmaker() as session:
        try:
            yield session
        finally:
            await session.close()
            
def get_sync_session():
    """Генератор синхронной сессии для работы с базой данных."""
    session = SyncSession()
    try:
        yield session
    finally:
        session.close()

def create_tables():
    pass
    # logger.info("Все таблицы удалены")
    # Base.metadata.drop_all(engine_sync)
    # Base.metadata.create_all(engine_sync, checkfirst=True)
    # logger.info("Все таблицы созданы")
    from app.models.categories import Categories
    
    product_categories = {
        "Молочные продукты": [],
        "Овощи": [],
        "Крупы": [],
        "Бытовая химия": [],
        "Лекарства": [],
        "Готовая еда": [],
        "Перекусы": [],
        "Энергетики": [],
        "Фрукты": [],
        "Детские товары": [],
        "Экопродукты": [],
        "Сезонные товары": []
    }
    
    with engine_sync.connect() as conn:
        existing = conn.execute(select(Categories)).first()

        if existing is None:
            for name, products in product_categories.items():
                conn.execute(
                    insert(Categories).values(name=name, products=products)
                )
            conn.commit()
    
        print("Все таблицы созданы и заполнены начальными данными.")