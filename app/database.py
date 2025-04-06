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
    # logger.info("Все таблицы удалены")
    # Base.metadata.drop_all(engine_sync)
    # Base.metadata.create_all(engine_sync, checkfirst=True)
    # logger.info("Все таблицы созданы")
    from app.models.categories import Categories
    
    product_categories = {
        "Молочные продукты": ["молоко", "сыр", "творог", "сливки", "йогурты", "сметана", "кефир", "ряженка", "топлёное молоко"],
        "Овощи": ["картофель", "помидоры", "огурцы", "капуста", "морковь", "свёкла", "лук", "чеснок", "перец", "кабачки"],
        "Крупы": ["гречка", "рис", "пшено", "овсянка", "макароны", "ячневая крупа", "перловка", "булгур", "кускус"],
        "Бытовая химия": ["моющее средство", "чистящие средства", "стиральный порошок", "освежитель воздуха", "губки", "щётки", "бумажные полотенца"],
        "Лекарства": ["парацетамол", "ибупрофен", "аспирин", "витамины", "противогриппозные средства", "капли от насморка", "пластыри", "бинты"],
        "Готовая еда": ["пельмени", "замороженные пиццы", "готовые супы", "котлеты", "блины", "чебуреки", "шаурма", "роллы"],
        "Перекусы": ["снэки", "чипсы", "батончики", "орехи", "сухофрукты", "попкорн", "печенье", "вяленое мясо"],
        "Энергетики": ["энергетики", "кофе в банках", "чай в бутылках", "ледяной кофе", "газировка"],
        "Фрукты": ["яблоки", "бананы", "груши", "апельсины", "киви", "виноград", "мандарины", "ананас", "манго", "гранат"],
        "Детские товары": ["пюре детское", "подгузники", "корм для детей", "соски", "бутылочки", "детские каши", "влажные салфетки"],
        "Экопродукты": ["соевое молоко", "миндальное молоко", "гречневая лапша", "растительный йогурт", "тофу", "эко-крупы", "натуральные соки"],
        "Сезонные товары": ["арбуз", "клубника", "черешня", "шампуры", "уголь", "новогодние украшения", "елочные игрушки", "пасхальные яйца", "снегокат"]
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