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

base_url = "http://localhost:8082"

for category_name, category_data in product_categories.items():
    # Формируем JSON для создания стеллажа
    shelf_payload = {
        "name": category_name,
        "map_id": 1,
        "category": category_name,
        "color_hex": "#AAAAAA",  # пример цвета, можно изменить
        "x": random.randint(0, 20),
        "y": 1,
        "z": random.randint(0, 20)
    }
    
    # Создаём стеллаж
    shelf_response = requests.post(f"{base_url}/shelves", json=shelf_payload)
    
    if shelf_response.status_code == 200 or shelf_response.status_code == 201:
        # Допустим, что ID стеллажа возвращается в JSON поле "id"
        shelf_id = shelf_response.json().get("id")
        print(f"Стеллаж '{category_name}' создан. ID = {shelf_id}.")
        
        # Проходимся по каждому продукту внутри категории
        for product_name in category_data["products"]:
            product_payload = {
                "name": product_name,
                "shelf_id": shelf_id,
                "color_hex": "#FF0000",  # можно изменить цвет
                "percent_discount": None,
                "time_discount_start": None,
                "time_discount_end": None
            }
            
            product_response = requests.post(f"{base_url}/products", json=product_payload)
            if product_response.status_code == 200 or product_response.status_code == 201:
                print(f"  Продукт '{product_name}' успешно добавлен в стеллаж (ID {shelf_id}).")
            else:
                print(f"  Ошибка при добавлении продукта '{product_name}': {product_response.text}")
    else:
        print(f"Ошибка при создании стеллажа '{category_name}': {shelf_response.text}")


