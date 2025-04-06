import requests

# Определяем 7 категорий с типичными товарами
product_categories = {
    "Молочные продукты": {
        "products": ["молоко", "сыр", "творог", "кефир", "сливки"]
    },
    "Овощи": {
        "products": ["картофель", "помидоры", "огурцы", "морковь", "капуста"]
    },
    "Фрукты": {
        "products": ["яблоки", "бананы", "груши", "киви", "апельсины"]
    },
    "Сезонные товары": {
        "products": ["арбуз", "дыня", "слива", "персики", "виноград"]
    },
    "Перекусы": {
        "products": ["чипсы", "сухарики", "орехи", "сухофрукты", "печенье"]
    },
    "Готовая еда": {
        "products": ["пельмени", "суп", "котлета", "блины", "пицца"]
    },
    "Лекарства": {
        "products": ["парацетамол", "аспирин", "ибупрофен", "витамины", "противогриппозные средства"]
    }
}

base_url = "https://api.melzik.ru"
map_id = 5

# Задаем позиции стеллажей вручную в пределах 20x20
# Координаты (x, z) подобраны так, чтобы:
# - Передняя часть (ближе к входу): меньшие значения z
# - Задняя часть: большие значения z
shelf_positions = {
    "Молочные продукты": (4, 4),    # Передняя левая часть
    "Овощи": (12, 4),               # Передняя центральная часть
    "Фрукты": (18, 4),              # Передняя правая часть
    "Сезонные товары": (4, 12),     # Левый сектор центральной части
    "Перекусы": (12, 12),           # Центр магазина
    "Готовая еда": (18, 12),        # Правый сектор центральной части
    "Лекарства": (12, 18)           # Задняя центральная часть
}

# Создаем стеллажи и добавляем товары
for category, data in product_categories.items():
    if category not in shelf_positions:
        print(f"Нет позиции для категории {category}")
        continue
    x, z = shelf_positions[category]
    
    shelf_payload = {
        "name": category,
        "map_id": map_id,
        "capacity": 15,
        "category": category,
        "color_hex": "#00FF00",  # зеленый цвет для стеллажей
        "x": x,
        "y": 1,
        "z": z
    }
    
    shelf_response = requests.post(f"{base_url}/shelves", json=shelf_payload)
    
    if shelf_response.status_code in (200, 201):
        shelf_id = shelf_response.json().get("id")
        print(f"Стеллаж '{category}' создан. ID = {shelf_id}.")
        
        # Добавляем товары в стеллаж
        for product in data["products"]:
            product_payload = {
                "name": product,
                "shelf_id": shelf_id,
                "color_hex": "#0000FF",  # синий цвет для товаров
                "percent_discount": None,
                "time_discount_start": None,
                "time_discount_end": None
            }
            product_response = requests.post(f"{base_url}/products", json=product_payload)
            if product_response.status_code in (200, 201):
                print(f"  Продукт '{product}' успешно добавлен.")
            else:
                print(f"  Ошибка при добавлении '{product}': {product_response.text}")
    else:
        print(f"Ошибка при создании стеллажа '{category}': {shelf_response.text}")

# Добавляем кассу.
# В реальном магазине касса часто располагается ближе к входу.
cashier_payload = {
    "name": "Касса 1",
    "map_id": map_id,
    "x": 10,  # примерно по центру по горизонтали
    "z": 2    # ближе к входу (меньшее значение z)
}

cashier_response = requests.post(f"{base_url}/kasses", json=cashier_payload)
if cashier_response.status_code in (200, 201):
    print("Касса успешно добавлена.")
else:
    print(f"Ошибка при добавлении кассы: {cashier_response.text}")
