import random
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
from pydantic import BaseModel


class CustomerProfile(BaseModel):
    name: str
    age: int
    segment: str
    motives: List[str]
    preferences: List[str]
    fears: List[str]
    shopping_list: List[str]
    budget_allocation: Dict[str, float]


class CustomerGenerator:
    def __init__(self):
        self.segments = [
            {
                "name": "Молодые семьи с детьми",
                "age_range": (25, 40),
                "motives": ["удобство", "экономия", "качество продуктов для семьи"],
                "preferences": ["Молочные продукты", "Детские товары", "Овощи"],
                "fears": ["некачественные продукты", "мало ассортимента для детей", "высокие цены"],
                "budget_allocation": {
                    "Молочные продукты": 0.20,
                    "Детские товары": 0.20,
                    "Овощи": 0.15,
                    "Крупы": 0.10,
                    "Лекарства": 0.05,
                    "Готовая еда": 0.01,
                    "Сезонные товары": 0.01,
                    "Перекусы": 0.01,
                }
            },
            {
                "name": "Работающие люди",
                "age_range": (20, 50),
                "motives": ["быстрота", "доступность", "готовые решения"],
                "preferences": ["Готовая еда", "Перекусы", "Энергетики"],
                "fears": ["очереди", "мало готовой еды", "неудобство"],
                "budget_allocation": {
                    "Готовая еда": 0.35,
                    "Перекусы": 0.25,
                    "Энергетики": 0.20,
                    "Молочные продукты": 0.05,
                    "Овощи": 0.01,
                    "Сезонные товары": 0.01,
                    "Лекарства": 0.01,
                    "Крупы": 0.01,
                }
            },
            {
                "name": "Пенсионеры",
                "age_range": (60, 80),
                "motives": ["дешево", "качество", "всё в одном месте"],
                "preferences": ["Крупы", "Молочные продукты", "Овощи"],
                "fears": ["непонятные акции", "физические сложности", "нет скидок"],
                "budget_allocation": {
                    "Крупы": 0.30,
                    "Молочные продукты": 0.25,
                    "Овощи": 0.20,
                    "Лекарства": 0.30,
                    "Сезонные товары": 0.01,
                }
            },
            {
                "name": "Молодёжь",
                "age_range": (16, 25),
                "motives": ["доступность", "снеки", "трендовые товары"],
                "preferences": ["Экопродукты", "Перекусы", "Энергетики"],
                "fears": ["нет новинок", "неприкольный магазин", "мало фишек"],
                "budget_allocation": {
                    "Экопродукты": 0.05,
                    "Перекусы": 0.15,
                    "Энергетики": 0.15,
                    "Молочные продукты": 0.0,
                    "Овощи": 0.0,
                    "Сезонные товары": 0.0,
                }
            },
            {
                "name": "Люди из пригородов",
                "age_range": (30, 65),
                "motives": ["закуп впрок", "низкие цены", "широкий выбор"],
                "preferences": ["Крупы", "Бытовая химия", "Овощи"],
                "fears": ["дорого", "мало товара", "нет доставки"],
                "budget_allocation": {
                    "Крупы": 0.35,
                    "Бытовая химия": 0.15,
                    "Овощи": 0.20,
                    "Молочные продукты": 0.10,
                    "Лекарства": 0.05,
                    "Готовая еда": 0.02,
                    "Сезонные товары": 0.10,
                }
            },
        ]

        self.product_categories = {
            "Молочные продукты": {"products": [
                "молоко", "сыр", "творог", "сливки", "йогурты",
                "сметана", "кефир", "ряженка", "топлёное молоко"
            ]},
            "Овощи": {"products": [
                "картофель", "помидоры", "огурцы", "капуста", "морковь",
                "свёкла", "лук", "чеснок", "перец", "кабачки"
            ]},
            "Крупы": {"products": [
                "гречка", "рис", "пшено", "овсянка", "макароны",
                "ячневая крупа", "перловка", "булгур", "кускус"
            ]},
            "Бытовая химия": {"products": [
                "моющее средство", "чистящие средства", "стиральный порошок",
                "освежитель воздуха", "губки", "щётки", "бумажные полотенца"
            ]},
            "Лекарства": {"products": [
                "парацетамол", "ибупрофен", "аспирин", "витамины",
                "противогриппозные средства", "капли от насморка", "пластыри", "бинты"
            ]},
            "Готовая еда": {"products": [
                "пельмени", "замороженные пиццы", "готовые супы",
                "котлеты", "блины", "чебуреки", "шаурма", "роллы"
            ]},
            "Перекусы": {"products": [
                "снэки", "чипсы", "батончики", "орехи", "сухофрукты",
                "попкорн", "печенье", "вяленое мясо"
            ]},
            "Энергетики": {"products": [
                "энергетики", "кофе в банках", "чай в бутылках", "ледяной кофе", "газировка"
            ]},
            "Фрукты": {"products": [
                "яблоки", "бананы", "груши", "апельсины", "киви",
                "виноград", "мандарины", "ананас", "манго", "гранат"
            ]},
            "Детские товары": {"products": [
                "пюре детское", "подгузники", "корм для детей",
                "соски", "бутылочки", "детские каши", "влажные салфетки"
            ]},
            "Экопродукты": {"products": [
                "соевое молоко", "миндальное молоко", "гречневая лапша",
                "растительный йогурт", "тофу", "эко-крупы", "натуральные соки"
            ]},
            "Сезонные товары": {"products": [
                "арбуз", "клубника", "черешня", "шампуры", "уголь", "новогодние украшения",
                "елочные игрушки", "пасхальные яйца", "снегокат"
            ]}
        }

    async def generate_preferences(self, segment, budget):
        # Симуляция асинхронной операции (например, обращение к базе данных)
        await asyncio.sleep(0)
        preferences = []
        for category, allocation in budget.items():
            if allocation < 0.05:
                continue
            variance = random.uniform(0.8, 1.2)
            adjusted_allocation = allocation * variance

            if category in segment["preferences"]:
                products = self.product_categories[category]["products"]
                count_products = max(1, int(adjusted_allocation * len(products)))
                preferences += random.sample(products, k=min(count_products, len(products)))
            else:
                products = self.product_categories[category]["products"]
                count_products = max(1, int(adjusted_allocation * len(products) * 0.5))
                preferences += random.sample(products, k=min(count_products, len(products)))
        return preferences

    async def generate_customer(self, i: int) -> Dict:
        # Симуляция асинхронной операции
        await asyncio.sleep(0)
        segment = random.choice(self.segments)
        age = random.randint(*segment["age_range"])
        name = f"Клиент_{i + 1}"
        motives = random.sample(segment["motives"], k=min(2, len(segment["motives"])))
        fears = random.sample(segment["fears"], k=min(2, len(segment["fears"])))
        preferences = await self.generate_preferences(segment, segment["budget_allocation"])
        shopping_list_size = random.randint(5, 12)
        shopping_list = random.sample(preferences, k=min(len(preferences), shopping_list_size))

        customer = CustomerProfile(
            name=name,
            age=age,
            segment=segment["name"],
            motives=motives,
            preferences=preferences,
            fears=fears,
            shopping_list=shopping_list,
            budget_allocation=segment["budget_allocation"],
        )
        return customer.model_dump()

    async def generate_customers(self, count: int) -> List[Dict]:
        tasks = [asyncio.create_task(self.generate_customer(i)) for i in range(count)]
        customers = await asyncio.gather(*tasks)
        return customers