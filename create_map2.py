import math
import random
import requests

# Новый набор категорий и товаров
new_product_categories = {
    "Напитки": {"weight": 1.0, "products": [
        "вода", "сок", "лимонад", "энергетик", "чай", "кофе"
    ]},
    "Снэки": {"weight": 0.8, "products": [
        "чипсы", "сухарики", "орешки", "попкорн", "сухофрукты"
    ]},
    "Замороженные продукты": {"weight": 0.6, "products": [
        "мороженое", "замороженные овощи", "замороженное мясо", "пельмени", "пицца"
    ]},
    "Выпечка": {"weight": 0.7, "products": [
        "хлеб", "булочки", "круассаны", "пирожные", "кексы"
    ]},
    "Косметика": {"weight": 0.5, "products": [
        "шампунь", "мыло", "лосьон", "крем", "маска для лица"
    ]}
}

base_url = "https://api.melzik.ru"
map_id = 2

# Параметры для сетки магазина 20x20
grid_size = 20
num_categories = len(new_product_categories)
grid_width = 3  # число стеллажей по горизонтали
num_rows = math.ceil(num_categories / grid_width)

# Задаём отступ от границ
start_x, start_z = 2, 2

# Вычисляем шаг по оси x так, чтобы максимальное значение не превышало grid_size
if grid_width > 1:
    step_x = (grid_size - start_x) / (grid_width - 1)
else:
    step_x = 0

# Аналогично по оси z
if num_rows > 1:
    step_z = (grid_size - start_z) / (num_rows - 1)
else:
    step_z = 0

# Вычисляем позиции для каждого стеллажа
positions = []
for i in range(num_categories):
    row = i // grid_width
    col = i % grid_width
    x = start_x + col * step_x
    z = start_z + row * step_z
    positions.append((x, z))

# Расстановка стеллажей с новыми категориями
for (i, (category_name, category_data)) in enumerate(new_product_categories.items()):
    x, z = positions[i]
    
    shelf_payload = {
        "name": category_name,
        "map_id": map_id,
        "capacity": 15,  # увеличена вместимость
        "category": category_name,
        "color_hex": "#00FF00",  # изменён цвет для наглядности
        "x": x,
        "y": 1,
        "z": z
    }
    
    shelf_response = requests.post(f"{base_url}/shelves", json=shelf_payload)
    
    if shelf_response.status_code in (200, 201):
        shelf_id = shelf_response.json().get("id")
        print(f"Стеллаж '{category_name}' создан. ID = {shelf_id}.")
        
        # Добавление товаров для этой категории
        for product_name in category_data["products"]:
            product_payload = {
                "name": product_name,
                "shelf_id": shelf_id,
                "color_hex": "#0000FF",  # другой цвет для товаров
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

# Добавление кассы с изменёнными координатами (убедимся, что координаты кассы тоже внутри 20x20)
cashier_payload = {
    "name": "Касса 1",
    "map_id": map_id,
    "x": 15,  # подобрано значение, чтобы быть в пределах сетки
    "z": 15
}

cashier_response = requests.post(f"{base_url}/shelves", json=cashier_payload)
if cashier_response.status_code in (200, 201):
    print("Касса успешно добавлена.")
else:
    print(f"Ошибка при добавлении кассы: {cashier_response.text}")
