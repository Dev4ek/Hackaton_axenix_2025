import requests

# Категории с продуктами (пример реальных товаров)
product_categories = {
    "Сезонные товары": {
        "weight": 1.0,
        "products": ["арбуз", "клубника", "черешня", "яблоко", "апельсин"]
    },
    "Фрукты": {
        "weight": 0.8,
        "products": ["бананы", "киви", "виноград", "манго", "груша"]
    },
    "Перекусы": {
        "weight": 0.6,
        "products": ["чипсы", "сухарики", "орешки", "сухофрукты", "печенье"]
    },
    "Лекарства": {
        "weight": 0.7,
        "products": ["парацетамол", "ибупрофен", "аспирин", "витамины", "противогриппозные средства"]
    },
    "Готовая еда": {
        "weight": 0.5,
        "products": ["пельмени", "замороженная пицца", "суп", "котлета", "блины"]
    }
}

base_url = "https://api.melzik.ru"
map_id = 3

# Задаём позиции для стеллажей, подобранные вручную
# (x, z) гарантированно в пределах 20x20 и имитируют реалистичное расположение:
# например, стеллажи у входа (фронт) и в глубине магазина (задняя часть)
shelf_positions = {
    "Сезонные товары": (3, 3),   # возле входа
    "Фрукты": (10, 3),           # центральная зона передней части
    "Перекусы": (17, 3),         # правый угол передней части
    "Лекарства": (5, 17),        # левая задняя часть
    "Готовая еда": (15, 17)      # правая задняя часть
}

# Создаём стеллажи и добавляем товары для каждой категории
for category_name, category_data in product_categories.items():
    # Получаем позицию для данной категории
    if category_name not in shelf_positions:
        print(f"Нет позиции для категории '{category_name}'")
        continue
    x, z = shelf_positions[category_name]
    
    shelf_payload = {
        "name": category_name,
        "map_id": map_id,
        "capacity": 15,
        "category": category_name,
        "color_hex": "#00FF00",  # для стеллажей выбран зеленый цвет
        "x": x,
        "y": 1,
        "z": z
    }
    
    shelf_response = requests.post(f"{base_url}/shelves", json=shelf_payload)
    
    if shelf_response.status_code in (200, 201):
        shelf_id = shelf_response.json().get("id")
        print(f"Стеллаж '{category_name}' создан. ID = {shelf_id}.")
        
        # Добавляем товары в созданный стеллаж
        for product_name in category_data["products"]:
            product_payload = {
                "name": product_name,
                "shelf_id": shelf_id,
                "color_hex": "#0000FF",  # для товаров выбран синий цвет
                "percent_discount": None,
                "time_discount_start": None,
                "time_discount_end": None
            }
            product_response = requests.post(f"{base_url}/products", json=product_payload)
            if product_response.status_code in (200, 201):
                print(f"  Продукт '{product_name}' успешно добавлен.")
            else:
                print(f"  Ошибка при добавлении '{product_name}': {product_response.text}")
    else:
        print(f"Ошибка при создании стеллажа '{category_name}': {shelf_response.text}")

# Добавление кассы (расположим ее, например, в центре магазина)
cashier_payload = {
    "name": "Касса 1",
    "map_id": map_id,
    "x": 10,
    "z": 10
}

cashier_response = requests.post(f"{base_url}/kasses", json=cashier_payload)
if cashier_response.status_code in (200, 201):
    print("Касса успешно добавлена.")
else:
    print(f"Ошибка при добавлении кассы: {cashier_response.text}")
