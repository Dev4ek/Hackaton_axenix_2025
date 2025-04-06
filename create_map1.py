import random
import requests

product_categories = {
    "Молочные продукты": {"weight": 1.0, "products": [
        "молоко", "сыр", "творог", "сливки", "йогурты",
        "сметана", "кефир", "ряженка", "топлёное молоко"
    ]},
    "Овощи": {"weight": 0.8, "products": [
        "картофель", "помидоры", "огурцы", "капуста", "морковь",
        "свёкла", "лук", "чеснок", "перец", "кабачки"
    ]},
    "Крупы": {"weight": 0.6, "products": [
        "гречка", "рис", "пшено", "овсянка", "макароны",
        "ячневая крупа", "перловка", "булгур", "кускус"
    ]},
    "Бытовая химия": {"weight": 0.5, "products": [
        "моющее средство", "чистящие средства", "стиральный порошок",
        "освежитель воздуха", "губки", "щётки", "бумажные полотенца"
    ]},
    "Лекарства": {"weight": 0.3, "products": [
        "парацетамол", "ибупрофен", "аспирин", "витамины",
        "противогриппозные средства", "капли от насморка", "пластыри", "бинты"
    ]},
    "Готовая еда": {"weight": 0.9, "products": [
        "пельмени", "замороженные пиццы", "готовые супы",
        "котлеты", "блины", "чебуреки", "шаурма", "роллы"
    ]},
    "Перекусы": {"weight": 0.7, "products": [
        "снэки", "чипсы", "батончики", "орехи", "сухофрукты",
        "попкорн", "печенье", "вяленое мясо"
    ]},
    "Энергетики": {"weight": 0.4, "products": [
        "энергетики", "кофе в банках", "чай в бутылках", "ледяной кофе", "газировка"
    ]},
    "Фрукты": {"weight": 0.8, "products": [
        "яблоки", "бананы", "груши", "апельсины", "киви",
        "виноград", "мандарины", "ананас", "манго", "гранат"
    ]},
    "Детские товары": {"weight": 0.6, "products": [
        "пюре детское", "подгузники", "корм для детей",
        "соски", "бутылочки", "детские каши", "влажные салфетки"
    ]},
    "Экопродукты": {"weight": 0.7, "products": [
        "соевое молоко", "миндальное молоко", "гречневая лапша",
        "растительный йогурт", "тофу", "эко-крупы", "натуральные соки"
    ]},
    "Сезонные товары": {"weight": 0.2, "products": [
        "арбуз", "клубника", "черешня", "шампуры", "уголь", "новогодние украшения",
        "елочные игрушки", "пасхальные яйца", "снегокат"
    ]}
}
# base_url = "http://localhost:8082"
base_url = "https://api.melzik.ru"
map_id = 1

# Параметры сетки
start_x, start_z = 2, 2
step_x, step_z = 5, 5
grid_width = 4  # сколько стеллажей по горизонтали

positions = []
for i in range(len(product_categories)):
    row = i // grid_width
    col = i % grid_width
    x = start_x + col * step_x
    z = start_z + row * step_z
    positions.append((x, z))

# Расстановка стеллажей
for (i, (category_name, category_data)) in enumerate(product_categories.items()):
    x, z = positions[i]

    shelf_payload = {
        "name": category_name,
        "map_id": map_id,
        "capacity": 10,
        "category": category_name,
        "color_hex": "#AAAAAA",
        "x": x,
        "y": 1,
        "z": z
    }

    shelf_response = requests.post(f"{base_url}/shelves", json=shelf_payload)

    if shelf_response.status_code in (200, 201):
        shelf_id = shelf_response.json().get("id")
        print(f"Стеллаж '{category_name}' создан. ID = {shelf_id}.")

        for product_name in category_data["products"]:
            product_payload = {
                "name": product_name,
                "shelf_id": shelf_id,
                "color_hex": "#FF0000",
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

# Добавление кассы
cashier_payload = {
    "name": "Касса 1",
    "map_id": map_id,
    "x": 18,
    "z": 18
}

cashier_response = requests.post(f"{base_url}/shelves", json=cashier_payload)
if cashier_response.status_code in (200, 201):
    print("Касса успешно добавлена.")
else:
    print(f"Ошибка при добавлении кассы: {cashier_response.text}")