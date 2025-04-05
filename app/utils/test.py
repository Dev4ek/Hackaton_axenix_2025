import random
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
    visit_time: datetime


class CustomerGenerator:
    def __init__(self):
        self.segments = [
            {
                "name": "Молодые семьи с детьми",
                "age_range": (25, 40),
                "motives": ["удобство", "экономия", "качество продуктов для семьи"],
                "preferences": ["Молочные продукты", "Детские товары", "Овощи"],
                "fears": ["некачественные продукты", "мало ассортимента для детей", "высокие цены"],
            },
            {
                "name": "Работающие люди",
                "age_range": (20, 50),
                "motives": ["быстрота", "доступность", "готовые решения"],
                "preferences": ["Готовая еда", "Перекусы", "Энергетики"],
                "fears": ["очереди", "мало готовой еды", "неудобство"],
            },
            {
                "name": "Пенсионеры",
                "age_range": (60, 80),
                "motives": ["дешево", "качество", "всё в одном месте"],
                "preferences": ["Крупы", "Молочные продукты", "Овощи"],
                "fears": ["непонятные акции", "физические сложности", "нет скидок"],
            },
            {
                "name": "Молодёжь",
                "age_range": (16, 25),
                "motives": ["доступность", "снеки", "трендовые товары"],
                "preferences": ["Экопродукты", "Перекусы", "Энергетики"],
                "fears": ["нет новинок", "неприкольный магазин", "мало фишек"],
            },
            {
                "name": "Люди из пригородов",
                "age_range": (30, 65),
                "motives": ["закуп впрок", "низкие цены", "широкий выбор"],
                "preferences": ["Крупы", "Бытовая химия", "Овощи"],
                "fears": ["дорого", "мало товара", "нет доставки"],
            },
        ]

        self.product_categories = {
            "Молочные продукты": {"weight": 1.0, "products": ["молоко", "сыр", "творог", "сливки", "йогурты"]},
            "Овощи": {"weight": 0.8, "products": ["картофель", "помидоры", "огурцы", "капуста", "морковь"]},
            "Крупы": {"weight": 0.6, "products": ["гречка", "рис", "пшено", "овсянка", "макароны"]},
            "Бытовая химия": {"weight": 0.5, "products": ["моющее средство", "чистящие средства", "моющее для посуды", "стиральный порошок"]},
            "Лекарства": {"weight": 0.3, "products": ["парацетамол", "ибупрофен", "аспирин", "витамины", "противогриппозные средства"]},
            "Готовая еда": {"weight": 0.9, "products": ["пельмени", "картопляники", "замороженные пиццы", "готовые супы"]},
            "Перекусы": {"weight": 0.7, "products": ["снэки", "чипсы", "батончики", "орехи", "сухофрукты"]},
            "Энергетики": {"weight": 0.4, "products": ["энергетики", "кофе в банках", "чай в бутылках"]},
            "Фрукты": {"weight": 0.8, "products": ["яблоки", "бананы", "груши", "апельсины", "киви"]},
            "Детские товары": {"weight": 0.6, "products": ["пюре детское", "подгузники", "корм для детей", "соски", "бутылочки"]},
        }

    def add_category(self, category_name: str, products: List[str], weight: float):
        """Добавляет новую категорию с весом и товарами в продуктовый словарь."""
        self.product_categories[category_name] = {"weight": weight, "products": products}
        # Обновляем preferences клиентов с учётом новой категории
        for segment in self.segments:
            if category_name not in segment["preferences"]:
                segment["preferences"].append(category_name)

    def add_product_to_category(self, category_name: str, product_name: str):
        """Добавляет новый товар в существующую категорию."""
        if category_name in self.product_categories:
            self.product_categories[category_name]["products"].append(product_name)
            # Обновляем preferences клиентов с учётом нового товара в категории
            for segment in self.segments:
                if category_name in segment["preferences"]:
                    if product_name not in segment["preferences"]:
                        segment["preferences"].append(product_name)
        else:
            print(f"Категория {category_name} не существует.")

    def generate_customers(self, count: int) -> List[CustomerProfile]:
        customers = []
        base_time = datetime.now().replace(hour=9, minute=0)

        for i in range(count):
            segment = random.choice(self.segments)
            age = random.randint(*segment["age_range"])
            name = f"Клиент_{i + 1}"
            motives = random.sample(segment["motives"], k=min(2, len(segment["motives"])))
            fears = random.sample(segment["fears"], k=min(2, len(segment["fears"])))

            # Генерация предпочтений на основе веса категорий
            preferences = []
            category_weights = {k: v["weight"] for k, v in self.product_categories.items()}
            preferred_categories = random.choices(
                list(category_weights.keys()), 
                weights=list(category_weights.values()), 
                k=3
            )
            
            # Добавляем товары из выбранных категорий
            for category in preferred_categories:
                if category in segment["preferences"]:
                    products = self.product_categories[category]["products"]
                    preferences += random.sample(products, k=2)  # Выбираем 2 случайных товара из категории

            # Генерация покупок с учётом предпочтений
            shopping_list = preferences.copy()

            # Время прихода с интервалами по 3-10 минут
            visit_time = base_time + timedelta(minutes=random.randint(3 * i, 10 * (i + 1)))

            customer = CustomerProfile(
                name=name,
                age=age,
                segment=segment["name"],
                motives=motives,
                preferences=preferences,
                fears=fears,
                shopping_list=shopping_list,
                visit_time=visit_time
            )
            customers.append(customer)

        return customers


if __name__ == "__main__":
    generator = CustomerGenerator()

    # Пример добавления новой категории и товара
    generator.add_category("Замороженные продукты", ["мороженое", "замороженные овощи", "пельмени"], 0.7)
    generator.add_product_to_category("Замороженные продукты", "замороженная рыба")

    # Генерация клиентов с учётом новых данных
    clients = generator.generate_customers(count=5)

    for c in clients:
        print(c)
