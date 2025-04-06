import asyncio
import numpy as np
import random
import json
from collections import deque, defaultdict
from typing import List, Dict
from pydantic import BaseModel

# Настройка seed для воспроизводимости
SPONTANEOUS_BASE_CHANCE = 0.25  # вероятность спонтанной покупки

# Вероятности и бонусы для покупки
BASE_PURCHASE_CHANCE = 0.15      # немного повышена базовая вероятность покупки
MOTIVE_BONUS = 0.15              # бонус за мотивацию "дешево" оставляем умеренным
FEAR_PENALTY = 0.35              # штраф за отсутствие скидок
DISCOUNT_BONUS = 0.15            # бонус за скидку
PREFERENCE_BONUS = 0.15          # бонус за совпадение предпочтений
BUDGET_BONUS_FACTOR = 0.25       # бонус от бюджета оставляем без изменений

# Порог, ниже которого клиент не идёт к полке
MIN_CHANCE_TO_APPROACH = 0.302  # сниженный порог, чтобы покупка происходила чаще

# Время перемещения и обслуживания
BLOCK_TIME_SECONDS = 0.5
OPEN_TIME_SECONDS = 8 * 3600
CLOSE_TIME_SECONDS = 20 * 3600
QUEUE_SERVICE_TIME = 8

# Настройки очереди и касс
MAX_QUEUE_LENGTH_DEFAULT = 5
KASSA_BREAK_PROB = 0.0002  # вероятность поломки касс

# Масштаб времени симуляции
SIMULATION_SCALE = 0.000002

# Размер групп клиентов
GROUP_SIZE_NON_PEAK = 5
GROUP_SIZE_PEAK = 15

####################################
#         Классы и генерация      #
####################################
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
        # Определяем сегменты с весами (сумма должна равняться 1)
        self.segments = [
            {
                "name": "Молодые семьи с детьми",
                "age_range": (25, 40),
                "motives": ["удобство", "экономия", "качество продуктов для семьи"],
                "preferences": ["Молочные продукты", "Детские товары", "Овощи"],
                "fears": ["некачественные продукты", "мало ассортимента для детей", "высокие цены"],
                "budget_allocation": {
                    "Готовая еда": 0.10,
                    "Перекусы": 0.10,
                    "Энергетики": 0.10,
                    "Молочные продукты": 0.20,
                    "Овощи": 0.20,
                    "Сезонные товары": 0.10,
                    "Лекарства": 0.20,
                    "Крупы": 0.20,
                    "Бытовая химия": 0.15,
                    "Фрукты": 0.15,
                    "Детские товары": 0.25,
                    "Экопродукты": 0.10,
                }
            },
            {
                "name": "Работающие люди",
                "age_range": (20, 50),
                "motives": ["быстрота", "доступность", "готовые решения"],
                "preferences": ["Готовая еда", "Перекусы", "Энергетики"],
                "fears": ["очереди", "мало готовой еды", "неудобство"],
                "budget_allocation": {
                   "Готовая еда": 0.20,
                    "Перекусы": 0.20,
                    "Энергетики": 0.20,
                    "Молочные продукты": 0.10,
                    "Овощи": 0.10,
                    "Сезонные товары": 0.10,
                    "Лекарства": 0.10,
                    "Крупы": 0.10,
                    "Бытовая химия": 0.10,
                    "Фрукты": 0.10,
                    "Детские товары": 0.01,
                    "Экопродукты": 0.10,
                }
            },
            {
                "name": "Пенсионеры",
                "age_range": (60, 80),
                "motives": ["дешево", "качество", "всё в одном месте"],
                "preferences": ["Крупы", "Молочные продукты", "Овощи"],
                "fears": ["непонятные акции", "физические сложности", "нет скидок"],
                "budget_allocation": {
                    "Готовая еда": 0.10,
                    "Перекусы": 0.10,
                    "Энергетики": 0.01,
                    "Молочные продукты": 0.20,
                    "Овощи": 0.20,
                    "Сезонные товары": 0.20,
                    "Лекарства": 0.30,
                    "Крупы": 0.20,
                    "Бытовая химия": 0.10,
                    "Фрукты": 0.20,
                    "Детские товары": 0.20,
                    "Экопродукты": 0.20,
                }
            },
            {
                "name": "Молодёжь",
                "age_range": (16, 25),
                "motives": ["доступность", "снеки", "трендовые товары"],
                "preferences": ["Экопродукты", "Перекусы", "Энергетики"],
                "fears": ["нет новинок", "неприкольный магазин", "мало фишек"],
                "budget_allocation": {
                    "Готовая еда": 0.20,
                    "Перекусы": 0.20,
                    "Энергетики": 0.20,
                    "Молочные продукты": 0.10,
                    "Овощи": 0.10,
                    "Сезонные товары": 0.15,
                    "Лекарства": 0.10,
                    "Крупы": 0.10,
                    "Бытовая химия": 0.10,
                    "Фрукты": 0.10,
                    "Детские товары": 0.00,
                    "Экопродукты": 0.20,
                }
            },
            {
                "name": "Люди из пригородов",
                "age_range": (30, 65),
                "motives": ["закуп впрок", "низкие цены", "широкий выбор"],
                "preferences": ["Крупы", "Бытовая химия", "Овощи"],
                "fears": ["дорого", "мало товара", "нет доставки"],
                "budget_allocation": {
                   "Готовая еда": 0.10,
                    "Перекусы": 0.10,
                    "Энергетики": 0.10,
                    "Молочные продукты": 0.10,
                    "Овощи": 0.10,
                    "Сезонные товары": 0.20,
                    "Лекарства": 0.20,
                    "Крупы": 0.20,
                    "Бытовая химия": 0.20,
                    "Фрукты": 0.10,
                    "Детские товары": 0.10,
                    "Экопродукты": 0.10,
                }
            },
        ]
        # Задаём веса для выбора сегмента (сумма весов = 1)
        self.segment_weights = [0.2, 0.4, 0.2, 0.1, 0.1]

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

    def generate_age(self, age_range):
        # Реалистичное распределение возраста: центр + нормальное отклонение
        center = (age_range[0] + age_range[1]) / 2
        std = (age_range[1] - age_range[0]) / 6
        age = int(np.random.normal(center, std))
        return max(age_range[0], min(age_range[1], age))

    async def generate_preferences(self, segment, budget):
        await asyncio.sleep(0)
        preferences = []
        for category, allocation in budget.items():
            if allocation < 0.05:
                continue
            variance = random.uniform(0.8, 1.3)
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
        await asyncio.sleep(0)
        # Выбор сегмента с учетом весов
        segment = random.choices(self.segments, weights=self.segment_weights, k=1)[0]
        age = self.generate_age(segment["age_range"])
        name = f"Клиент_{i + 1}"
        # Динамическая генерация мотивов и страхов
        motives = random.sample(segment["motives"], k=random.randint(1, min(3, len(segment["motives"]))))
        fears = random.sample(segment["fears"], k=random.randint(1, min(3, len(segment["fears"]))))
        preferences = await self.generate_preferences(segment, segment["budget_allocation"])
        # Размер списка покупок зависит от сегмента
        if segment["name"] == "Работающие люди":
            shopping_list_size = random.randint(4, 8)
        elif segment["name"] == "Молодые семьи с детьми":
            shopping_list_size = random.randint(7, 14)
        else:
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

####################################
#         Вспомогательные функции #
####################################
def bfs_path(grid_width, grid_height, start, end, occupied_positions):
    if start == end:
        return [start]
    visited = set()
    queue = deque()
    parents = {}
    visited.add(start)
    queue.append(start)
    while queue:
        x, z = queue.popleft()
        for dx, dz in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, nz = x + dx, z + dz
            if 0 <= nx < grid_width and 0 <= nz < grid_height:
                if (nx, nz) == end:
                    parents[(nx, nz)] = (x, z)
                    path = []
                    cur = (nx, nz)
                    while cur != start:
                        path.append(cur)
                        cur = parents[cur]
                    path.append(start)
                    path.reverse()
                    return path
                if (nx, nz) not in visited and (nx, nz) not in occupied_positions:
                    visited.add((nx, nz))
                    parents[(nx, nz)] = (x, z)
                    queue.append((nx, nz))
    return None

def manhattan_distance(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def move_along_path(path_cells, current_time, current_occupied, cell_visits,
                    grid_width, grid_height,
                    block_time=BLOCK_TIME_SECONDS, close_time=CLOSE_TIME_SECONDS):
    destination = path_cells[-1]
    path_log = []
    position = path_cells[0]
    current_occupied.add(position)
    path_log.append({"x": position[0], "z": position[1], "time": current_time})
    cell_visits[position] += 1
    i = 1
    while i < len(path_cells):
        next_cell = path_cells[i]
        if next_cell in current_occupied and next_cell != destination:
            new_path = bfs_path(grid_width, grid_height, position, destination, current_occupied)
            if not new_path or len(new_path) < 2:
                return position, current_time, "no_path", path_log
            path_cells = new_path
            i = 1
            continue
        current_occupied.remove(position)
        position = next_cell
        current_occupied.add(position)
        current_time += block_time
        if current_time > close_time:
            status = "store_closed"
            path_log.append({"x": position[0], "z": position[1], "time": current_time})
            return position, current_time, status, path_log
        path_log.append({"x": position[0], "z": position[1], "time": current_time})
        cell_visits[position] += 1
        i += 1
    return position, current_time, "ok", path_log

####################################
#         Симуляция магазина     #
####################################
class StoreSimulation:
    def __init__(self, store_schema, max_queue_length=MAX_QUEUE_LENGTH_DEFAULT,
                 grid_width=20, grid_height=20):
        self.store_schema = store_schema
        self.shelves, self.kasses, self.item_map = self.load_store(store_schema)
        self.shelf_info = {}
        for shelf in store_schema['shelves']:
            x = shelf['x']
            z = shelf['z']
            width = shelf.get("width", 3)
            depth = shelf.get("depth", 1)
            cells = [(x + i, z + j) for i in range(width) for j in range(depth)]
            self.shelf_info[tuple(cells[0])] = {
                "category": shelf.get("category"),
                "attraction": shelf.get("attraction", 0.5),
                "products": shelf.get("products", []),
                "cells": cells
            }
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.max_queue_length = max_queue_length
        self.base_occupied_positions = set()
        for shelf in store_schema['shelves']:
            x = shelf['x']
            z = shelf['z']
            width = shelf.get("width", 3)
            depth = shelf.get("depth", 1)
            for i in range(width):
                for j in range(depth):
                    self.base_occupied_positions.add((x + i, z + j))
        for kassa in store_schema['kasses']:
            self.base_occupied_positions.add((kassa['x'], kassa['z']))
        self.queues = [[] for _ in self.kasses]
        self.cell_visits = defaultdict(int)
        self.shelf_purchases = defaultdict(int)
        self.global_stats = {
            "total_purchases": 0,
            "motive_trigger_count": 0,
            "fear_trigger_count": 0,
            "discount_trigger_count": 0,
            "kassa_breakdowns": 0,
            "left_due_to_queue": 0,
            "store_closed": 0,
            "no_kassa": 0,
            "no_path_to_kassa": 0,
            "no_path_to_shelf": 0,
            "no_start_position": 0,
            "completed": 0
        }
        self.current_occupied = set(self.base_occupied_positions)
        self.state_lock = asyncio.Lock()

    def load_store(self, store_schema):
        shelves = {}
        kasses = []
        item_map = {}
        for shelf in store_schema['shelves']:
            cat = shelf['category']
            x = shelf['x']
            z = shelf['z']
            width = shelf.get("width", 3)
            depth = shelf.get("depth", 1)
            cells = [(x + i, z + j) for i in range(width) for j in range(depth)]
            shelves[cat] = cells
            if 'products' in shelf:
                for product in shelf['products']:
                    product_info = {
                        "id": product.get('id'),
                        "name": product.get('name'),
                        "percent_discount": product.get('percent_discount'),
                        "time_discount_start": product.get('time_discount_start'),
                        "time_discount_end": product.get('time_discount_end')
                    }
                    item_map[product['name'].lower()] = (cat, cells, product_info)
        for kassa in store_schema['kasses']:
            kasses.append((kassa['x'], kassa['z']))
        return shelves, kasses, item_map

    def compute_purchase_chance(self, client, cat, product_info, shelf_quality=1.0):
        chance = BASE_PURCHASE_CHANCE * shelf_quality
        if any("дешево" in m.lower() for m in client.get('motives', [])):
            disc = product_info.get('percent_discount')
            if disc and disc > 0:
                chance += MOTIVE_BONUS
        if any("нет скидок" in f.lower() for f in client.get('fears', [])):
            disc = product_info.get('percent_discount')
            if not disc or disc == 0:
                chance -= FEAR_PENALTY
        disc = product_info.get('percent_discount')
        if disc and disc > 0:
            chance += (disc / 10.0) * DISCOUNT_BONUS
        preferences = [p.lower() for p in client.get('preferences', [])]
        if product_info.get('name') and product_info["name"].lower() in preferences:
            chance += PREFERENCE_BONUS
        allocation_bonus = client.get('budget_allocation', {}).get(cat, 0) * BUDGET_BONUS_FACTOR
        chance += allocation_bonus
        return max(0.0, min(1.0, chance))

    async def simulate_client(self, client, wait_for_arrival=True):
        if wait_for_arrival:
            await asyncio.sleep((client['arrival_time'] - OPEN_TIME_SECONDS) * SIMULATION_SCALE)
        current_time = client['arrival_time']
        status = "completed"
        path_log = []
        purchases_log = []
        position = (0, 0)
        async with self.state_lock:
            if position in self.current_occupied:
                found_alt = False
                for dx in range(self.grid_width):
                    candidate = (dx, 0)
                    if candidate not in self.current_occupied:
                        position = candidate
                        found_alt = True
                        break
                if not found_alt:
                    self.global_stats["no_start_position"] += 1
                    return {"client": client['name'], "path": path_log, "purchases": purchases_log, "end_time": current_time, "status": "no_start_position"}
            self.current_occupied.add(position)
        path_log.append({"x": position[0], "z": position[1], "time": current_time, "event": "entered_store"})
        self.cell_visits[position] += 1

        for item in client.get('shopping_list', []):
            if current_time > CLOSE_TIME_SECONDS:
                status = "store_closed"
                self.global_stats["store_closed"] += 1
                break
            item_lower = item.lower()
            if item_lower not in self.item_map:
                continue
            cat, shelf_cells, product_info = self.item_map[item_lower]
            visits = sum(self.cell_visits.get(cell, 0) for cell in shelf_cells) / len(shelf_cells)
            shelf_quality = 0.7 if visits < 5 else 1.0
            chance = self.compute_purchase_chance(client, cat, product_info, shelf_quality)
            if chance < MIN_CHANCE_TO_APPROACH:
                continue
            async with self.state_lock:
                target_cell = shelf_cells[0]
                path_cells = bfs_path(self.grid_width, self.grid_height, position, target_cell, self.current_occupied)
                if not path_cells:
                    status = "no_path_to_shelf"
                    self.global_stats["no_path_to_shelf"] += 1
                    break
                final_pos, new_time, st, move_log = move_along_path(path_cells, current_time, self.current_occupied, self.cell_visits, self.grid_width, self.grid_height)
                position = final_pos
                current_time = new_time
                path_log.extend(move_log[1:])
            if st in ('store_closed', "no_path") or current_time > CLOSE_TIME_SECONDS:
                status = "store_closed" if current_time > CLOSE_TIME_SECONDS else "no_path_to_shelf"
                self.global_stats[status] += 1
                break

            path_log[-1]["event"] = f"arrived_shelf ({cat})"
            purchased = random.random() < chance
            purchase_record = {"item": item, "x": position[0], "z": position[1], "time": current_time, "chance": chance, "purchased": purchased}
            purchases_log.append(purchase_record)
            if purchased:
                self.global_stats["total_purchases"] += 1
                for cell in shelf_cells:
                    self.shelf_purchases[cell] += 1
                path_log[-1]["purchase_item"] = item
                path_log[-1]["purchase_chance"] = round(chance, 3)
                path_log[-1]["event"] += f"; PURCHASED: {item}"
            else:
                path_log[-1]["purchase_item"] = item
                path_log[-1]["purchase_chance"] = round(chance, 3)
                path_log[-1]["event"] += f"; DID_NOT_BUY: {item}"

            # Спонтанные покупки для соседних полок
            for shelf_coords, shelf_data in self.shelf_info.items():
                if shelf_coords == shelf_cells[0]:
                    continue
                if manhattan_distance(position, shelf_coords) == 1:
                    if shelf_data.get("attraction", 0.5) >= 0.7:
                        spontaneous_chance = SPONTANEOUS_BASE_CHANCE * shelf_data.get("attraction", 0.5)
                        if random.random() < spontaneous_chance:
                            if shelf_data.get("products"):
                                product = random.choice(shelf_data["products"])
                                purchase_record = {
                                    "item": product.get("name", "unknown"),
                                    "x": shelf_coords[0],
                                    "z": shelf_coords[1],
                                    "time": current_time,
                                    "chance": spontaneous_chance,
                                    "purchased": True,
                                    "spontaneous": True
                                }
                                purchases_log.append(purchase_record)
                                self.global_stats["total_purchases"] += 1
                                for cell in shelf_data["cells"]:
                                    self.shelf_purchases[cell] += 1
                                path_log.append({
                                    "x": shelf_coords[0],
                                    "z": shelf_coords[1],
                                    "time": current_time,
                                    "event": f"spontaneous_purchase: {product.get('name', 'unknown')}"
                                })

        if status not in ("store_closed", "no_path_to_shelf"):
            async with self.state_lock:
                best_score = None
                chosen_kassa = None
                for i, kassa_pos in enumerate(self.kasses):
                    dist = manhattan_distance(position, kassa_pos)
                    score = dist + len(self.queues[i])
                    if best_score is None or score < best_score:
                        best_score = score
                        chosen_kassa = i
                if chosen_kassa is None:
                    status = "no_kassa"
                    self.global_stats["no_kassa"] += 1
                else:
                    if random.random() < KASSA_BREAK_PROB:
                        self.global_stats["kassa_breakdowns"] += 1
                        status = "kassa_broken"
                        path_log.append({"x": position[0], "z": position[1], "time": current_time, "event": "kassa_broken"})
                        self.current_occupied.remove(position)
                        return {"client": client['name'], "path": path_log, "purchases": purchases_log, "end_time": current_time, "status": status}
                    if len(self.queues[chosen_kassa]) >= self.max_queue_length:
                        status = "left_due_to_queue"
                        self.global_stats["left_due_to_queue"] += 1
                    else:
                        kassa_pos = self.kasses[chosen_kassa]
                        path_cells = bfs_path(self.grid_width, self.grid_height, position, kassa_pos, self.current_occupied)
                        if not path_cells:
                            status = "no_path_to_kassa"
                            self.global_stats["no_path_to_kassa"] += 1
                        else:
                            final_pos, new_time, st, move_log = move_along_path(path_cells, current_time, self.current_occupied, self.cell_visits, self.grid_width, self.grid_height)
                            position = final_pos
                            current_time = new_time
                            path_log.extend(move_log[1:])
                            if st == 'store_closed' or current_time > CLOSE_TIME_SECONDS:
                                status = "store_closed"
                                self.global_stats["store_closed"] += 1
                            else:
                                self.queues[chosen_kassa].append(client['name'])
                                queue_wait_time = len(self.queues[chosen_kassa]) * QUEUE_SERVICE_TIME
                                current_time += queue_wait_time
                                path_log.append({"x": position[0], "z": position[1], "time": current_time, "event": f"finished queue at Kassa {chosen_kassa+1}"})
                                if current_time > CLOSE_TIME_SECONDS:
                                    status = "store_closed"
                                    self.global_stats["store_closed"] += 1
                                if client['name'] in self.queues[chosen_kassa]:
                                    self.queues[chosen_kassa].remove(client['name'])
        async with self.state_lock:
            if position in self.current_occupied:
                self.current_occupied.remove(position)
        if status == "completed":
            self.global_stats["completed"] += 1
        return {"client": client['name'], "path": path_log, "purchases": purchases_log, "end_time": current_time, "status": status}

    async def simulate_clients(self, clients):
        total_clients = len(clients)
        peak_start = 12 * 3600
        peak_end = 14 * 3600
        peak_clients = [c for c in clients if random.random() < 0.4]
        non_peak_clients = [c for c in clients if c not in peak_clients]
        for client in peak_clients:
            client.update({'arrival_time': random.uniform(peak_start, peak_end)})
        open_time = OPEN_TIME_SECONDS
        close_time = CLOSE_TIME_SECONDS
        morning = [c for c in non_peak_clients if random.random() < 0.5]
        evening = [c for c in non_peak_clients if c not in morning]
        for client in morning:
            client['arrival_time'] = random.uniform(open_time, peak_start)
        for client in evening:
            client['arrival_time'] = random.uniform(peak_end, close_time)
        clients_sorted = sorted(clients, key=lambda c: c['arrival_time'])
        def group_clients(client_list, group_size):
            groups = []
            for i in range(0, len(client_list), group_size):
                groups.append(client_list[i:i+group_size])
            return groups
        morning_groups = group_clients([c for c in clients_sorted if c['arrival_time'] < peak_start], GROUP_SIZE_NON_PEAK)
        peak_groups = group_clients([c for c in clients_sorted if peak_start <= c['arrival_time'] <= peak_end], GROUP_SIZE_PEAK)
        evening_groups = group_clients([c for c in clients_sorted if c['arrival_time'] > peak_end], GROUP_SIZE_NON_PEAK)
        all_groups = morning_groups + peak_groups + evening_groups
        results = []
        last_group_avg = open_time
        for group in all_groups:
            group_avg = sum(c['arrival_time'] for c in group) / len(group)
            delay = (group_avg - last_group_avg) * SIMULATION_SCALE
            if delay > 0:
                await asyncio.sleep(delay)
            tasks = [asyncio.create_task(self.simulate_client(client, wait_for_arrival=False)) for client in group]
            group_results = await asyncio.gather(*tasks)
            results.extend(group_results)
            last_group_avg = group_avg
        stats = {
            "total_clients": len(clients),
            "completed": self.global_stats["completed"],
            "left_due_to_queue": self.global_stats["left_due_to_queue"],
            "store_closed": self.global_stats["store_closed"],
            "no_kassa": self.global_stats["no_kassa"],
            "no_path_to_kassa": self.global_stats["no_path_to_kassa"],
            "no_path_to_shelf": self.global_stats["no_path_to_shelf"],
            "no_start_position": self.global_stats["no_start_position"],
            "total_purchases": self.global_stats["total_purchases"],
            "motive_trigger_count": self.global_stats["motive_trigger_count"],
            "fear_trigger_count": self.global_stats["fear_trigger_count"],
            "discount_trigger_count": self.global_stats["discount_trigger_count"],
            "kassa_breakdowns": self.global_stats["kassa_breakdowns"]
        }
        popular_zones = sorted(
            [{"x": k[0], "z": k[1], "visits": v} for k, v in self.cell_visits.items()],
            key=lambda d: d['visits'],
            reverse=True
        )
        shelf_statistics = {}
        for shelf in self.store_schema.get("shelves", []):
            x = shelf["x"]
            z = shelf["z"]
            width = shelf.get("width", 3)
            depth = shelf.get("depth", 1)
            cells = [(x + i, z + j) for i in range(width) for j in range(depth)]
            visits = sum(self.cell_visits.get(cell, 0) for cell in cells)
            purchases = sum(self.shelf_purchases.get(cell, 0) for cell in cells)
            conversion = (purchases / visits) if visits > 0 else 0
            shelf_statistics[str(cells[0])] = {
                "category": shelf["category"],
                "cells": cells,
                "visits": visits,
                "purchases": purchases,
                "conversion_rate": round(conversion, 3)
            }
        recommendations = self.generate_recommendations(stats, popular_zones)
        print(stats)
        return {
            "results": results,
            "statistics": stats,
            "shelf_statistics": shelf_statistics,
            "popular_zones": popular_zones,
            "recommendations": recommendations
        }

    def generate_recommendations(self, stats, popular_zones):
        recommendations = []
        if stats["left_due_to_queue"] > 0:
            recommendations.append("Некоторые клиенты уходят из-за очереди на кассе. Рекомендуется увеличить длину очереди или добавить дополнительную кассу.")
        if stats["kassa_breakdowns"] > 0:
            recommendations.append("Обнаружены сбои в работе касс. Проверьте оборудование или распределение нагрузки.")
        shelf_statistics = {}
        total_visits = 0
        total_purchases = 0
        shelf_count = 0
        for shelf in self.store_schema.get("shelves", []):
            x = shelf["x"]
            z = shelf["z"]
            width = shelf.get("width", 3)
            depth = shelf.get("depth", 1)
            cells = [(x + i, z + j) for i in range(width) for j in range(depth)]
            visits = sum(self.cell_visits.get(cell, 0) for cell in cells)
            purchases = sum(self.shelf_purchases.get(cell, 0) for cell in cells)
            conversion = (purchases / visits) if visits > 0 else 0
            shelf_statistics[str(cells[0])] = {
                "category": shelf["category"],
                "cells": cells,
                "visits": visits,
                "purchases": purchases,
                "conversion_rate": round(conversion, 3)
            }
            total_visits += visits
            total_purchases += purchases
            shelf_count += 1
        average_visits = total_visits / shelf_count if shelf_count > 0 else 0
        for shelf in self.store_schema.get("shelves", []):
            x = shelf["x"]
            z = shelf["z"]
            width = shelf.get("width", 3)
            depth = shelf.get("depth", 1)
            cells = [(x + i, z + j) for i in range(width) for j in range(depth)]
            visits = sum(self.cell_visits.get(cell, 0) for cell in cells)
            purchases = sum(self.shelf_purchases.get(cell, 0) for cell in cells)
            conversion = (purchases / visits) if visits > 0 else 0
            products = shelf.get("products", [])
            avg_discount = sum((p.get("percent_discount") or 0) for p in products) / len(products) if products else 0
            if visits < 0.5 * average_visits or conversion < 0.1:
                msg = f"Полка '{shelf['category']}' на {cells} имеет низкую посещаемость ({visits} посещений) и конверсию {conversion:.1%}"
                if avg_discount > 20:
                    msg += f", несмотря на высокие скидки (средняя скидка {avg_discount:.0f}%). Возможно, стоит изменить расположение или усилить акции."
                else:
                    msg += ". Рассмотрите изменение расположения или усиление акций для повышения интереса."
                recommendations.append(msg)
            elif conversion > (total_purchases / total_visits) * 1.5 and visits > average_visits:
                recommendations.append(f"Полка '{shelf['category']}' на {cells} показывает высокую конверсию ({conversion:.1%}). Рассмотрите возможность использования её в качестве якорной зоны.")
        return recommendations
    
###################################
# Пример запуска
###################################
async def main(count, store_data, categories_data):
    random.seed(42)
    generator = CustomerGenerator()
    clients = await generator.generate_customers(count)
    sim = StoreSimulation(store_data)
    results = await sim.simulate_clients(clients)
    def convert_np(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    

    for category in categories_data:
        generator.product_categories[category["name"]] = {"products": category["products"]}
    
    print(generator.product_categories)
    return json.dumps(results, ensure_ascii=False, indent=2, default=convert_np)

if __name__ == '__main__':
    with open('/home/milaha/Документы/Hackaton_axenix_2025/app/utils/kassas_updated.json', encoding='utf-8') as f:
        store_data = json.load(f)
    asyncio.run(main(150, store_data))
