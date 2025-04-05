import asyncio
import numpy as np
import random
import json
from collections import deque, defaultdict

###############################
#   CONSTANTS AND UTILITIES   #
###############################

BLOCK_TIME_SECONDS = 1                 # 1 блок = 4 секунды
OPEN_TIME_SECONDS = 6 * 3600 * 60        # 8:00 утра, в секундах от полуночи
CLOSE_TIME_SECONDS = 24 * 3600 * 60        # 20:00 вечера, в секундах от полуночи
QUEUE_SERVICE_TIME = 100                # 10 секунд на каждого клиента в очереди
MAX_QUEUE_LENGTH_DEFAULT = 100          # Максимальная длина очереди
BASE_PURCHASE_CHANCE = 1.0             # Базовая вероятность покупки товара
MOTIVE_BONUS = 0.2                     # Бонус к вероятности при совпадении мотива
FEAR_PENALTY = 0.01                    # Штраф к вероятности при срабатывании страха
DISCOUNT_BONUS = 0.1                  # Дополнительная прибавка на каждые 10% скидки
MIN_CHANCE_TO_APPROACH = 0.3           # Минимальная вероятность покупки, чтобы хотя бы подойти к полке

###############################
#   BFS: КРАТЧАЙШИЙ МАРШРУТ   #
###############################
def bfs_path(grid_width, grid_height, start, end, occupied_positions):
    """
    Ищем кратчайший путь от start до end (включая start и end) на сетке grid_width x grid_height.
    Разрешаем входить в end даже если она занята (полка/касса).

    Возвращаем список координат ([(x,z), (x,z), ...]) или None.

    ПРИМЕЧАНИЕ: Поиск не учитывает то, что одна клетка может освободиться позже.
    Это статический поиск пути при текущих занятых клетках.
    """
    if start == end:
        return [start]

    visited = set()
    queue = deque()
    parents = {}

    visited.add(start)
    queue.append(start)

    while queue:
        x, z = queue.popleft()
        for dx, dz in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, nz = x+dx, z+dz
            if 0 <= nx < grid_width and 0 <= nz < grid_height:
                # Если это end, разрешим вход
                if (nx, nz) == end:
                    parents[(nx,nz)] = (x,z)
                    path = []
                    cur = (nx, nz)
                    while cur != start:
                        path.append(cur)
                        cur = parents[cur]
                    path.append(start)
                    path.reverse()
                    return path
                # Иначе проверяем, что клетка не занята
                if (nx, nz) not in visited and (nx, nz) not in occupied_positions:
                    visited.add((nx,nz))
                    parents[(nx,nz)] = (x,z)
                    queue.append((nx,nz))
    return None


def manhattan_distance(p1, p2):
    return abs(p1[0]-p2[0]) + abs(p1[1]-p2[1])

###############################
#   STEP-BY-STEP MOVEMENT     #
###############################
def move_along_path(path_cells, current_time, current_occupied, cell_visits,
                    block_time=BLOCK_TIME_SECONDS, close_time=CLOSE_TIME_SECONDS):
    """
    Двигаемся ПОШАГОВО по path_cells, освобождая предыдущую клетку, занимая новую.
    Возвращает (последняя_позиция, текущее_время, status) и полный лог (список dict).

    status может быть 'ok' или 'store_closed', если время вышло.

    path_cells - полный путь (список координат, включая старт).
    """
    path_log = []
    position = path_cells[0]
    # Занимаем стартовую клетку
    current_occupied.add(position)
    path_log.append({"x": position[0], "z": position[1], "time": current_time})
    cell_visits[position] += 1

    status = 'ok'

    for cell in path_cells[1:]:
        # Освобождаем предыдущую клетку
        current_occupied.remove(position)

        # Переходим в новую клетку
        position = cell
        current_occupied.add(position)

        current_time += block_time
        if current_time > close_time:
            status = 'store_closed'
            break

        path_log.append({"x": position[0], "z": position[1], "time": current_time})
        cell_visits[position] += 1

    return position, current_time, status, path_log

###############################
#      StoreSimulation        #
###############################

class StoreSimulation:
    def __init__(self, store_schema, max_queue_length=MAX_QUEUE_LENGTH_DEFAULT,
                 grid_width=20, grid_height=20):
        """
        Расширенный реализм:
        - Поклеточное движение: move_along_path
        - Освобождаем клетку, когда уходим.
        - Если (nx, nz) занята, BFS вернет, что пути нет.
        - Клиенты ходят ПОСЛЕДОВАТЕЛЬНО (упрощение). Параллельность требует дополнительной логики.
        """
        self.store_schema = store_schema
        # загрузим полки, кассы и item_map
        self.shelves, self.kasses, self.item_map = self.load_store(store_schema)

        self.grid_width = grid_width
        self.grid_height = grid_height
        self.max_queue_length = max_queue_length

        # Каждая касса имеет очередь
        self.queues = [[] for _ in self.kasses]

        # Базово занятые клетки (полки, кассы)
        self.base_occupied_positions = set()
        for shelf in store_schema['shelves']:
            self.base_occupied_positions.add((shelf['x'], shelf['z']))
        for kassa in store_schema['kasses']:
            self.base_occupied_positions.add((kassa['x'], kassa['z']))

        # Счетчик посещений клеток
        self.cell_visits = defaultdict(int)

        # Дополнительная статистика
        self.global_stats = {
            "total_purchases": 0,
            "motive_trigger_count": 0,
            "fear_trigger_count": 0,
            "discount_trigger_count": 0
        }

        # Текущее состояние занятости клеток (перезаполняется при simulate_clients)
        self.current_occupied = set()

    def load_store(self, store_schema):
        shelves = {}
        kasses = []
        item_map = {}

        for shelf in store_schema['shelves']:
            cat = shelf['category']
            coords = (shelf['x'], shelf['z'])
            shelves[cat] = coords

            if 'products' in shelf:
                for product in shelf['products']:
                    item_name = product['name'].lower()
                    product_info = {
                        "id": product.get('id'),
                        "name": product.get('name'),
                        "percent_discount": product.get('percent_discount'),
                        "time_discount_start": product.get('time_discount_start'),
                        "time_discount_end": product.get('time_discount_end')
                    }
                    item_map[item_name] = (cat, coords, product_info)

        for kassa in store_schema['kasses']:
            kasses.append((kassa['x'], kassa['z']))

        return shelves, kasses, item_map

    def compute_purchase_chance(self, client, product_info):
        chance = BASE_PURCHASE_CHANCE
        triggered_motive = False
        triggered_fear = False
        triggered_discount = False

        # Мотив: "дешево" + есть скидка
        if any("дешево" in m.lower() for m in client.get('motives', [])):
            disc = product_info.get('percent_discount')
            if disc and disc > 0:
                chance += MOTIVE_BONUS
                triggered_motive = True

        # Страх: "нет скидок" + нет скидки
        if any("нет скидок" in f.lower() for f in client.get('fears', [])):
            disc = product_info.get('percent_discount')
            if not disc or disc == 0:
                chance -= FEAR_PENALTY
                triggered_fear = True

        # Скидка
        disc = product_info.get('percent_discount')
        if disc and disc > 0:
            triggered_discount = True
            chance += (disc/10.0)*DISCOUNT_BONUS

        # Глобальная статистика
        if triggered_motive:
            self.global_stats["motive_trigger_count"] += 1
        if triggered_fear:
            self.global_stats["fear_trigger_count"] += 1
        if triggered_discount:
            self.global_stats["discount_trigger_count"] += 1

        # Ограничиваем [0..1]
        chance = max(0.0, min(1.0, chance))
        return chance

    async def simulate_client(self, client,start_position = (0, 0), start_time=OPEN_TIME_SECONDS):
        """
        Поклеточная симуляция:
        1) Проверяем, свободна ли стартовая клетка (0,0). Если нет, ищем свободную на (dx,0).
        2) Идём к каждой полке, если chance>MIN_CHANCE_TO_APPROACH.
           Путь ищем BFS. Потом move_along_path.
           Если в процессе время вышло, return store_closed.
           В конце шага добавляем дополнительное событие: "arrived_shelf".
        3) Логируем покупку прямо в path, чтобы было видно, когда и где купил.
        4) В конце идем к кассе.
        5) Становимся в очередь, добавляем время.
        """
        current_time = start_time
        status = "completed"

        path_log = []  # объединим все шаги и события
        purchases_log = []

        # Начальная позиция start_position
        position = start_position
        # Ищем, если занято
        if position in self.current_occupied:
            found_alt = False
            for dx in range(self.grid_width):
                candidate = (dx, 0)
                if candidate not in self.current_occupied:
                    position = candidate
                    found_alt = True
                    break
            if not found_alt:
                return {
                    "client": client['name'],
                    "path": path_log,
                    "purchases": purchases_log,
                    "end_time": current_time,
                    "status": "no_start_position"
                }

        # Занимаем эту клетку
        self.current_occupied.add(position)
        path_log.append({"x": position[0], "z": position[1], "time": current_time, "event": "entered_store"})
        self.cell_visits[position] += 1

        # Проходим по shopping_list
        for item in client.get('shopping_list', []):
            if current_time > CLOSE_TIME_SECONDS:
                status = "store_closed"
                break

            item_lower = item.lower()
            if item_lower not in self.item_map:
                continue

            cat, shelf_pos, product_info = self.item_map[item_lower]

            # Проверим budget_allocation
            if cat not in client.get('budget_allocation', {}):
                continue

            chance = self.compute_purchase_chance(client, product_info)
            if chance < MIN_CHANCE_TO_APPROACH:
                # пропускаем
                continue

            # Ищем путь BFS
            path_cells = bfs_path(
                self.grid_width,
                self.grid_height,
                position,
                shelf_pos,
                self.current_occupied
            )
            if not path_cells:
                status = "no_path_to_shelf"
                break

            # Двигаемся поклеточно
            final_pos, new_time, st, move_log = move_along_path(
                path_cells,
                current_time,
                self.current_occupied,
                self.cell_visits
            )

            # Вставляем в path_log (пропуская дублирующую первую точку)
            if len(move_log) > 1:
                path_log.extend(move_log[1:])

            position = final_pos
            current_time = new_time

            if st == 'store_closed' or current_time > CLOSE_TIME_SECONDS:
                status = "store_closed"
                break

            # Здесь мы точно на полке, логируем событие "arrived_shelf"
            path_log[-1]["event"] = f"arrived_shelf ({cat})"

            # попытаемся купить
            purchased = (random.random() < chance)
            purchase_record = {
                "item": item,
                "x": position[0],
                "z": position[1],
                "time": current_time,
                "chance": chance,
                "purchased": purchased
            }
            purchases_log.append(purchase_record)

            # Чтобы также отобразить покупку в path, добавим новые поля
            if purchased:
                self.global_stats["total_purchases"] += 1
                path_log[-1]["purchase_item"] = item
                path_log[-1]["purchase_chance"] = round(chance, 3)
                path_log[-1]["event"] = (path_log[-1]["event"] + 
                                           f"; PURCHASED: {item}")
            else:
                path_log[-1]["purchase_item"] = item
                path_log[-1]["purchase_chance"] = round(chance, 3)
                path_log[-1]["event"] = (path_log[-1]["event"] + 
                                           f"; DID_NOT_BUY: {item}")

        # Если всё ок, идём к кассе
        if status not in ("store_closed", "no_path_to_shelf"):
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
            else:
                if len(self.queues[chosen_kassa]) >= self.max_queue_length:
                    status = "left_due_to_queue"
                else:
                    kassa_pos = self.kasses[chosen_kassa]
                    path_cells = bfs_path(
                        self.grid_width,
                        self.grid_height,
                        position,
                        kassa_pos,
                        self.current_occupied
                    )
                    if not path_cells:
                        status = "no_path_to_kassa"
                    else:
                        final_pos, new_time, st, move_log = move_along_path(
                            path_cells,
                            current_time,
                            self.current_occupied,
                            self.cell_visits
                        )
                        if len(move_log) > 1:
                            path_log.extend(move_log[1:])

                        position = final_pos
                        current_time = new_time

                        if st == 'store_closed' or current_time > CLOSE_TIME_SECONDS:
                            status = "store_closed"
                        else:
                            # очередь
                            self.queues[chosen_kassa].append(client['name'])
                            queue_wait_time = len(self.queues[chosen_kassa]) * QUEUE_SERVICE_TIME
                            current_time += queue_wait_time
                            path_log.append({
                                "x": position[0], "z": position[1], "time": current_time,
                                "event": f"finished queue at Kassa {chosen_kassa+1}"
                            })
                            if current_time > CLOSE_TIME_SECONDS:
                                status = "store_closed"

        return {
            "client": client['name'],
            "path": path_log,
            "purchases": purchases_log,
            "end_time": current_time,
            "status": status
        }

    async def simulate_clients(self, clients):
        # Копируем базовые занятые
        self.current_occupied = set(self.base_occupied_positions)

        results = []
        for client in clients:
            r = await self.simulate_client(client)
            results.append(r)

        completed = sum(1 for r in results if r['status'] == 'completed')
        left_due_to_queue = sum(1 for r in results if r['status'] == 'left_due_to_queue')
        store_closed = sum(1 for r in results if r['status'] == 'store_closed')
        no_kassa = sum(1 for r in results if r['status'] == 'no_kassa')
        no_path_to_kassa = sum(1 for r in results if r['status'] == 'no_path_to_kassa')
        no_path_to_shelf = sum(1 for r in results if r['status'] == 'no_path_to_shelf')
        no_start_position = sum(1 for r in results if r['status'] == 'no_start_position')

        stats = {
            "total_clients": len(clients),
            "completed": completed,
            "left_due_to_queue": left_due_to_queue,
            "store_closed": store_closed,
            "no_kassa": no_kassa,
            "no_path_to_kassa": no_path_to_kassa,
            "no_path_to_shelf": no_path_to_shelf,
            "no_start_position": no_start_position,
            "total_purchases": self.global_stats["total_purchases"],
            "motive_trigger_count": self.global_stats["motive_trigger_count"],
            "fear_trigger_count": self.global_stats["fear_trigger_count"],
            "discount_trigger_count": self.global_stats["discount_trigger_count"]
        }

        # Популярные зоны
        popular_zones = sorted(
            [
                {"x": k[0], "z": k[1], "visits": v}
                for k, v in self.cell_visits.items()
            ],
            key=lambda d: d['visits'],
            reverse=True
        )

        return {
            "results": results,
            "statistics": stats,
            "popular_zones": popular_zones
        }

###################################
# Пример запуска
###################################
if __name__ == '__main__':
    import sys
    random.seed(42)

    with open('/home/milaha/Документы/Hackaton_axenix_2025/app/utils/kassas_updated.json', encoding='utf-8') as f:
        store_data = json.load(f)

    # Здесь полный список из 50 клиентов
    clients = [
        {
            "name": "Клиент_1", "age":72, "segment":"Пенсионеры",
            "motives":["качество", "дешево"],
            "preferences":["овсянка", "рис", "ряженка", "сметана", "чеснок", "ибупрофен"],
            "fears":["физические сложности", "непонятные акции"],
            "shopping_list":["овсянка", "рис", "сметана", "ряженка", "ибупрофен", "чеснок"],
            "budget_allocation": {"Крупы": 0.3, "Молочные продукты": 0.25, "Овощи": 0.2, "Лекарства": 0.3, "Сезонные товары": 0.01},
            "visit_time":39005.0
        },
        {
            "name":"Клиент_2", "age":47, "segment":"Люди из пригородов",
            "motives":["низкие цены", "закуп впрок"],
            "preferences":["кускус", "овсянка", "губки", "огурцы", "кефир", "пластыри", "шампуры"],
            "fears":["нет доставки", "дорого"],
            "shopping_list":["губки", "кускус", "шампуры", "пластыри", "кефир", "овсянка", "огурцы"],
            "budget_allocation":{"Крупы":0.35, "Бытовая химия":0.15, "Овощи":0.2, "Молочные продукты":0.1, "Лекарства":0.05, "Готовая еда":0.02, "Сезонные товары":0.1},
            "visit_time":35783.0
        },
        {
            "name":"Клиент_3", "age":25, "segment":"Молодые семьи с детьми",
            "motives":["экономия", "качество продуктов для семьи"],
            "preferences":["молоко", "влажные салфетки", "свёкла", "булгур", "пластыри"],
            "fears":["мало ассортимента для детей", "некачественные продукты"],
            "shopping_list":["булгур", "пластыри", "свёкла", "молоко", "влажные салфетки"],
            "budget_allocation": {"Молочные продукты":0.2, "Детские товары":0.2, "Овощи":0.15, "Крупы":0.1, "Лекарства":0.05, "Готовая еда":0.01, "Сезонные товары":0.01, "Перекусы":0.01},
            "visit_time":60830.0
        },
        {
            "name":"Клиент_4", "age":16, "segment":"Молодёжь",
            "motives":["доступность", "трендовые товары"],
            "preferences":["соевое молоко", "орехи", "энергетики"],
            "fears":["неприкольный магазин", "мало фишек"],
            "shopping_list":["энергетики", "соевое молоко", "орехи"],
            "budget_allocation": {"Экопродукты":0.05, "Перекусы":0.15, "Энергетики":0.15, "Молочные продукты":0.0, "Овощи":0.0, "Сезонные товары":0.0},
            "visit_time":53506.0
        },
        {
            "name":"Клиент_5", "age":36, "segment":"Работающие люди",
            "motives":["доступность", "готовые решения"],
            "preferences":["замороженные пиццы", "роллы", "вяленое мясо", "газировка", "ряженка"],
            "fears":["мало готовой еды", "неудобство"],
            "shopping_list":["роллы", "замороженные пиццы", "вяленое мясо", "газировка", "ряженка"],
            "budget_allocation":{"Готовая еда":0.35, "Перекусы":0.25, "Энергетики":0.2, "Молочные продукты":0.05, "Овощи":0.01, "Сезонные товары":0.01, "Лекарства":0.01, "Крупы":0.01},
            "visit_time":39743.0
        },
        {
            "name":"Клиент_6", "age":37, "segment":"Работающие люди",
            "motives":["доступность", "быстрота"],
            "preferences":["котлеты", "роллы", "попкорн", "газировка", "сметана"],
            "fears":["неудобство", "мало готовой еды"],
            "shopping_list":["сметана", "котлеты", "роллы", "газировка", "попкорн"],
            "budget_allocation":{"Готовая еда":0.35, "Перекусы":0.25, "Энергетики":0.2, "Молочные продукты":0.05, "Овощи":0.01, "Сезонные товары":0.01, "Лекарства":0.01, "Крупы":0.01},
            "visit_time":33855.0
        },
        {
            "name":"Клиент_7", "age":17, "segment":"Молодёжь",
            "motives":["доступность", "трендовые товары"],
            "preferences":["миндальное молоко", "батончики", "газировка"],
            "fears":["мало фишек", "неприкольный магазин"],
            "shopping_list":["миндальное молоко", "батончики", "газировка"],
            "budget_allocation":{"Экопродукты":0.05, "Перекусы":0.15, "Энергетики":0.15, "Молочные продукты":0.0, "Овощи":0.0, "Сезонные товары":0.0},
            "visit_time":47425.0
        },
        {
            "name":"Клиент_8", "age":63, "segment":"Пенсионеры",
            "motives":["всё в одном месте", "качество"],
            "preferences":["ячневая крупа", "макароны", "молоко", "сливки", "чеснок", "парацетамол"],
            "fears":["нет скидок", "непонятные акции"],
            "shopping_list":["сливки", "молоко", "чеснок", "ячневая крупа", "парацетамол", "макароны"],
            "budget_allocation":{"Крупы":0.3, "Молочные продукты":0.25, "Овощи":0.2, "Лекарства":0.3, "Сезонные товары":0.01},
            "visit_time":49540.0
        },
        {
            "name":"Клиент_9", "age":38, "segment":"Молодые семьи с детьми",
            "motives":["качество продуктов для семьи", "удобство"],
            "preferences":["ряженка", "корм для детей", "лук", "рис", "пластыри"],
            "fears":["некачественные продукты", "высокие цены"],
            "shopping_list":["ряженка", "рис", "пластыри", "корм для детей", "лук"],
            "budget_allocation":{"Молочные продукты":0.2, "Детские товары":0.2, "Овощи":0.15, "Крупы":0.1, "Лекарства":0.05, "Готовая еда":0.01, "Сезонные товары":0.01, "Перекусы":0.01},
            "visit_time":61829.0
        },
        {
            "name":"Клиент_10", "age":19, "segment":"Молодёжь",
            "motives":["снеки", "трендовые товары"],
            "preferences":["эко-крупы", "чипсы", "ледяной кофе"],
            "fears":["нет новинок", "неприкольный магазин"],
            "shopping_list":["ледяной кофе", "эко-крупы", "чипсы"],
            "budget_allocation":{"Экопродукты":0.05, "Перекусы":0.15, "Энергетики":0.15, "Молочные продукты":0.0, "Овощи":0.0, "Сезонные товары":0.0},
            "visit_time":60654.0
        },
        {
            "name":"Клиент_11", "age":75, "segment":"Пенсионеры",
            "motives":["дешево", "всё в одном месте"],
            "preferences":["рис", "кускус", "пшено", "топлёное молоко", "сметана", "огурцы", "аспирин"],
            "fears":["физические сложности", "непонятные акции"],
            "shopping_list":["топлёное молоко", "кускус", "огурцы", "пшено", "сметана", "аспирин", "рис"],
            "budget_allocation":{"Крупы":0.3, "Молочные продукты":0.25, "Овощи":0.2, "Лекарства":0.3, "Сезонные товары":0.01},
            "visit_time":59964.0
        },
        {
            "name":"Клиент_12", "age":26, "segment":"Молодые семьи с детьми",
            "motives":["экономия", "удобство"],
            "preferences":["сметана", "сливки", "соски", "морковь", "пшено", "капли от насморка"],
            "fears":["мало ассортимента для детей", "некачественные продукты"],
            "shopping_list":["капли от насморка", "пшено", "сливки", "соски", "сметана", "морковь"],
            "budget_allocation":{"Молочные продукты":0.2, "Детские товары":0.2, "Овощи":0.15, "Крупы":0.1, "Лекарства":0.05, "Готовая еда":0.01, "Сезонные товары":0.01, "Перекусы":0.01},
            "visit_time":67508.0
        },
        {
            "name":"Клиент_13", "age":19, "segment":"Молодёжь",
            "motives":["доступность", "трендовые товары"],
            "preferences":["натуральные соки", "батончики", "энергетики"],
            "fears":["нет новинок", "неприкольный магазин"],
            "shopping_list":["натуральные соки", "батончики", "энергетики"],
            "budget_allocation":{"Экопродукты":0.05, "Перекусы":0.15, "Энергетики":0.15, "Молочные продукты":0.0, "Овощи":0.0, "Сезонные товары":0.0},
            "visit_time":60779.0
        },
        {
            "name":"Клиент_14", "age":18, "segment":"Молодёжь",
            "motives":["снеки", "доступность"],
            "preferences":["соевое молоко", "сухофрукты", "газировка"],
            "fears":["нет новинок", "неприкольный магазин"],
            "shopping_list":["газировка", "соевое молоко", "сухофрукты"],
            "budget_allocation":{"Экопродукты":0.05, "Перекусы":0.15, "Энергетики":0.15, "Молочные продукты":0.0, "Овощи":0.0, "Сезонные товары":0.0},
            "visit_time":41901.0
        },
        {
            "name":"Клиент_15", "age":71, "segment":"Пенсионеры",
            "motives":["всё в одном месте", "дешево"],
            "preferences":["овсянка", "пшено", "йогурты", "сливки", "чеснок", "парацетамол"],
            "fears":["непонятные акции", "физические сложности"],
            "shopping_list":["парацетамол", "пшено", "йогурты", "овсянка", "сливки", "чеснок"],
            "budget_allocation":{"Крупы":0.3, "Молочные продукты":0.25, "Овощи":0.2, "Лекарства":0.3, "Сезонные товары":0.01},
            "visit_time":60561.0
        },
        {
            "name":"Клиент_16", "age":66, "segment":"Пенсионеры",
            "motives":["дешево", "всё в одном месте"],
            "preferences":["кускус", "макароны", "топлёное молоко", "сыр", "морковь", "аспирин"],
            "fears":["физические сложности", "нет скидок"],
            "shopping_list":["топлёное молоко", "сыр", "морковь", "кускус", "макароны"],
            "budget_allocation":{"Крупы":0.3, "Молочные продукты":0.25, "Овощи":0.2, "Лекарства":0.3, "Сезонные товары":0.01},
            "visit_time":37413.0
        },
        {
            "name":"Клиент_17", "age":16, "segment":"Молодёжь",
            "motives":["снеки", "трендовые товары"],
            "preferences":["соевое молоко", "орехи", "кофе в банках"],
            "fears":["нет новинок", "мало фишек"],
            "shopping_list":["орехи", "кофе в банках", "соевое молоко"],
            "budget_allocation":{"Экопродукты":0.05, "Перекусы":0.15, "Энергетики":0.15, "Молочные продукты":0.0, "Овощи":0.0, "Сезонные товары":0.0},
            "visit_time":67136.0
        },
        {
            "name":"Клиент_18", "age":25, "segment":"Работающие люди",
            "motives":["быстрота", "готовые решения"],
            "preferences":["замороженные пиццы", "чебуреки", "орехи", "газировка", "молоко"],
            "fears":["мало готовой еды", "очереди"],
            "shopping_list":["газировка", "замороженные пиццы", "чебуреки", "молоко", "орехи"],
            "budget_allocation":{"Готовая еда":0.35, "Перекусы":0.25, "Энергетики":0.2, "Молочные продукты":0.05, "Овощи":0.01, "Сезонные товары":0.01, "Лекарства":0.01, "Крупы":0.01},
            "visit_time":39904.0
        },
        {
            "name":"Клиент_19", "age":20, "segment":"Молодёжь",
            "motives":["трендовые товары", "доступность"],
            "preferences":["тофу", "чипсы", "кофе в банках"],
            "fears":["мало фишек", "нет новинок"],
            "shopping_list":["тофу", "чипсы", "кофе в банках"],
            "budget_allocation":{"Экопродукты":0.05, "Перекусы":0.15, "Энергетики":0.15, "Молочные продукты":0.0, "Овощи":0.0, "Сезонные товары":0.0},
            "visit_time":48359.0
        },
        {
            "name":"Клиент_20", "age":46, "segment":"Работающие люди",
            "motives":["быстрота", "готовые решения"],
            "preferences":["шаурма", "роллы", "чипсы", "снэки", "газировка", "сыр"],
            "fears":["очереди", "мало готовой еды"],
            "shopping_list":["сыр", "чипсы", "газировка", "снэки", "шаурма", "роллы"],
            "budget_allocation":{"Готовая еда":0.35, "Перекусы":0.25, "Энергетики":0.2, "Молочные продукты":0.05, "Овощи":0.01, "Сезонные товары":0.01, "Лекарства":0.01, "Крупы":0.01},
            "visit_time":61950.0
        },
        {
            "name":"Клиент_21", "age":19, "segment":"Молодёжь",
            "motives":["снеки", "доступность"],
            "preferences":["миндальное молоко", "попкорн", "ледяной кофе"],
            "fears":["мало фишек", "неприкольный магазин"],
            "shopping_list":["ледяной кофе", "попкорн", "миндальное молоко"],
            "budget_allocation":{"Экопродукты":0.05, "Перекусы":0.15, "Энергетики":0.15, "Молочные продукты":0.0, "Овощи":0.0, "Сезонные товары":0.0},
            "visit_time":49399.0
        },
        {
            "name":"Клиент_22", "age":32, "segment":"Молодые семьи с детьми",
            "motives":["экономия", "качество продуктов для семьи"],
            "preferences":["сыр", "корм для детей", "морковь", "гречка", "ибупрофен"],
            "fears":["некачественные продукты", "высокие цены"],
            "shopping_list":["сыр", "ибупрофен", "морковь", "гречка", "корм для детей"],
            "budget_allocation":{"Молочные продукты":0.2, "Детские товары":0.2, "Овощи":0.15, "Крупы":0.1, "Лекарства":0.05, "Готовая еда":0.01, "Сезонные товары":0.01, "Перекусы":0.01},
            "visit_time":63196.0
        },
        {
            "name":"Клиент_23", "age":36, "segment":"Молодые семьи с детьми",
            "motives":["удобство", "экономия"],
            "preferences":["творог", "детские каши", "морковь", "булгур", "капли от насморка"],
            "fears":["некачественные продукты", "мало ассортимента для детей"],
            "shopping_list":["детские каши", "морковь", "творог", "булгур", "капли от насморка"],
            "budget_allocation":{"Молочные продукты":0.2, "Детские товары":0.2, "Овощи":0.15, "Крупы":0.1, "Лекарства":0.05, "Готовая еда":0.01, "Сезонные товары":0.01, "Перекусы":0.01},
            "visit_time":42375.0
        },
        {
            "name":"Клиент_24", "age":35, "segment":"Люди из пригородов",
            "motives":["широкий выбор", "низкие цены"],
            "preferences":["овсянка", "гречка", "ячневая крупа", "бумажные полотенца", "огурцы", "кабачки", "сливки", "парацетамол", "арбуз"],
            "fears":["нет доставки", "мало товара"],
            "shopping_list":["огурцы", "сливки", "кабачки", "парацетамол", "бумажные полотенца", "ячневая крупа", "арбуз"],
            "budget_allocation":{"Крупы":0.35, "Бытовая химия":0.15, "Овощи":0.2, "Молочные продукты":0.1, "Лекарства":0.05, "Готовая еда":0.02, "Сезонные товары":0.1},
            "visit_time":64954.0
        },
        {
            "name":"Клиент_25", "age":72, "segment":"Пенсионеры",
            "motives":["всё в одном месте", "качество"],
            "preferences":["ячневая крупа", "пшено", "рис", "йогурты", "капуста", "противогриппозные средства"],
            "fears":["нет скидок", "непонятные акции"],
            "shopping_list":["противогриппозные средства", "пшено", "рис", "йогурты", "капуста", "ячневая крупа"],
            "budget_allocation":{"Крупы":0.3, "Молочные продукты":0.25, "Овощи":0.2, "Лекарства":0.3, "Сезонные товары":0.01},
            "visit_time":62580.0
        },
        {
            "name":"Клиент_26", "age":67, "segment":"Пенсионеры",
            "motives":["всё в одном месте", "качество"],
            "preferences":["ячневая крупа", "кускус", "сыр", "молоко", "морковь", "капли от насморка"],
            "fears":["нет скидок", "непонятные акции"],
            "shopping_list":["кускус", "морковь", "сыр", "капли от насморка", "молоко"],
            "budget_allocation":{"Крупы":0.3, "Молочные продукты":0.25, "Овощи":0.2, "Лекарства":0.3, "Сезонные товары":0.01},
            "visit_time":54446.0
        },
        {
            "name":"Клиент_27", "age":66, "segment":"Пенсионеры",
            "motives":["дешево", "качество"],
            "preferences":["перловка", "булгур", "йогурты", "творог", "перец", "ибупрофен"],
            "fears":["нет скидок", "непонятные акции"],
            "shopping_list":["перец", "йогурты", "перловка", "творог", "булгур", "ибупрофен"],
            "budget_allocation":{"Крупы":0.3, "Молочные продукты":0.25, "Овощи":0.2, "Лекарства":0.3, "Сезонные товары":0.01},
            "visit_time":34971.0
        },
        {
            "name":"Клиент_28", "age":74, "segment":"Пенсионеры",
            "motives":["дешево", "качество"],
            "preferences":["гречка", "ячневая крупа", "рис", "сливки", "огурцы", "пластыри"],
            "fears":["физические сложности", "нет скидок"],
            "shopping_list":["гречка", "рис", "огурцы", "сливки", "пластыри", "ячневая крупа"],
            "budget_allocation":{"Крупы":0.3, "Молочные продукты":0.25, "Овощи":0.2, "Лекарства":0.3, "Сезонные товары":0.01},
            "visit_time":72430.0
        },
        {
            "name":"Клиент_29", "age":39, "segment":"Молодые семьи с детьми",
            "motives":["качество продуктов для семьи", "экономия"],
            "preferences":["топлёное молоко", "сметана", "пюре детское", "морковь", "макароны", "аспирин"],
            "fears":["некачественные продукты", "мало ассортимента для детей"],
            "shopping_list":["аспирин", "морковь", "пюре детское", "топлёное молоко", "сметана"],
            "budget_allocation":{"Молочные продукты":0.2, "Детские товары":0.2, "Овощи":0.15, "Крупы":0.1, "Лекарства":0.05, "Готовая еда":0.01, "Сезонные товары":0.01, "Перекусы":0.01},
            "visit_time":50730.0
        },
        {
            "name":"Клиент_30", "age":63, "segment":"Люди из пригородов",
            "motives":["низкие цены", "широкий выбор"],
            "preferences":["рис", "кускус", "ячневая крупа", "моющее средство", "морковь", "йогурты", "пластыри", "шампуры"],
            "fears":["мало товара", "нет доставки"],
            "shopping_list":["рис", "кускус", "моющее средство", "йогурты", "пластыри", "морковь", "шампуры", "ячневая крупа"],
            "budget_allocation":{"Крупы":0.35, "Бытовая химия":0.15, "Овощи":0.2, "Молочные продукты":0.1, "Лекарства":0.05, "Готовая еда":0.02, "Сезонные товары":0.1},
            "visit_time":70986.0
        },
        {
            "name":"Клиент_31", "age":58, "segment":"Люди из пригородов",
            "motives":["закуп впрок", "низкие цены"],
            "preferences":["кускус", "овсянка", "гречка", "губки", "свёкла", "йогурты", "бинты", "арбуз"],
            "fears":["мало товара", "нет доставки"],
            "shopping_list":["кускус", "гречка", "свёкла", "йогурты", "бинты", "арбуз"],
            "budget_allocation":{"Крупы":0.35, "Бытовая химия":0.15, "Овощи":0.2, "Молочные продукты":0.1, "Лекарства":0.05, "Готовая еда":0.02, "Сезонные товары":0.1},
            "visit_time":65896.0
        },
        {
            "name":"Клиент_32", "age":66, "segment":"Пенсионеры",
            "motives":["всё в одном месте", "качество"],
            "preferences":["ячневая крупа", "рис", "сыр", "сливки", "морковь", "противогриппозные средства"],
            "fears":["физические сложности", "нет скидок"],
            "shopping_list":["сливки", "морковь", "противогриппозные средства", "сыр", "ячневая крупа", "рис"],
            "budget_allocation":{"Крупы":0.3, "Молочные продукты":0.25, "Овощи":0.2, "Лекарства":0.3, "Сезонные товары":0.01},
            "visit_time":62287.0
        },
        {
            "name":"Клиент_33", "age":65, "segment":"Пенсионеры",
            "motives":["дешево", "качество"],
            "preferences":["гречка", "кускус", "сливки", "ряженка", "огурцы", "помидоры", "витамины"],
            "fears":["нет скидок", "непонятные акции"],
            "shopping_list":["сливки", "кускус", "витамины", "ряженка", "помидоры", "огурцы", "гречка"],
            "budget_allocation":{"Крупы":0.3, "Молочные продукты":0.25, "Овощи":0.2, "Лекарства":0.3, "Сезонные товары":0.01},
            "visit_time":71040.0
        },
        {
            "name":"Клиент_34", "age":34, "segment":"Работающие люди",
            "motives":["доступность", "готовые решения"],
            "preferences":["котлеты", "чебуреки", "замороженные пиццы", "попкорн", "газировка", "сметана"],
            "fears":["мало готовой еды", "очереди"],
            "shopping_list":["сметана", "чебуреки", "попкорн", "котлеты", "газировка", "замороженные пиццы"],
            "budget_allocation":{"Готовая еда":0.35, "Перекусы":0.25, "Энергетики":0.2, "Молочные продукты":0.05, "Овощи":0.01, "Сезонные товары":0.01, "Лекарства":0.01, "Крупы":0.01},
            "visit_time":45294.0
        },
        {
            "name":"Клиент_35", "age":16, "segment":"Молодёжь",
            "motives":["доступность", "трендовые товары"],
            "preferences":["миндальное молоко", "чипсы", "чай в бутылках"],
            "fears":["нет новинок", "мало фишек"],
            "shopping_list":["чай в бутылках", "миндальное молоко", "чипсы"],
            "budget_allocation":{"Экопродукты":0.05, "Перекусы":0.15, "Энергетики":0.15, "Молочные продукты":0.0, "Овощи":0.0, "Сезонные товары":0.0},
            "visit_time":40961.0
        },
        {
            "name":"Клиент_36", "age":62, "segment":"Люди из пригородов",
            "motives":["широкий выбор", "закуп впрок"],
            "preferences":["ячневая крупа", "булгур", "пшено", "чистящие средства", "чеснок", "сливки", "бинты", "уголь"],
            "fears":["дорого", "мало товара"],
            "shopping_list":["уголь", "булгур", "ячневая крупа", "чеснок", "бинты", "чистящие средства", "сливки", "пшено"],
            "budget_allocation":{"Крупы":0.35, "Бытовая химия":0.15, "Овощи":0.2, "Молочные продукты":0.1, "Лекарства":0.05, "Готовая еда":0.02, "Сезонные товары":0.1},
            "visit_time":45255.0
        },
        {
            "name":"Клиент_37", "age":24, "segment":"Работающие люди",
            "motives":["готовые решения", "быстрота"],
            "preferences":["шаурма", "чебуреки", "чипсы", "кофе в банках", "кефир"],
            "fears":["мало готовой еды", "очереди"],
            "shopping_list":["кофе в банках", "кефир", "чипсы", "чебуреки", "шаурма"],
            "budget_allocation":{"Готовая еда":0.35, "Перекусы":0.25, "Энергетики":0.2, "Молочные продукты":0.05, "Овощи":0.01, "Сезонные товары":0.01, "Лекарства":0.01, "Крупы":0.01},
            "visit_time":39665.0
        },
        {
            "name":"Клиент_38", "age":56, "segment":"Люди из пригородов",
            "motives":["закуп впрок", "низкие цены"],
            "preferences":["ячневая крупа", "рис", "чистящие средства", "огурцы", "сливки", "витамины", "шампуры"],
            "fears":["дорого", "нет доставки"],
            "shopping_list":["рис", "сливки", "витамины", "ячневая крупа", "огурцы"],
            "budget_allocation":{"Крупы":0.35, "Бытовая химия":0.15, "Овощи":0.2, "Молочные продукты":0.1, "Лекарства":0.05, "Готовая еда":0.02, "Сезонные товары":0.1},
            "visit_time":52868.0
        },
        {
            "name":"Клиент_39", "age":67, "segment":"Пенсионеры",
            "motives":["качество", "дешево"],
            "preferences":["перловка", "кускус", "сметана", "ряженка", "свёкла", "капуста", "противогриппозные средства"],
            "fears":["физические сложности", "нет скидок"],
            "shopping_list":["перловка", "кускус", "ряженка", "сметана", "свёкла", "противогриппозные средства", "капуста"],
            "budget_allocation":{"Крупы":0.3, "Молочные продукты":0.25, "Овощи":0.2, "Лекарства":0.3, "Сезонные товары":0.01},
            "visit_time":37569.0
        },
        {
            "name":"Клиент_40", "age":52, "segment":"Люди из пригородов",
            "motives":["низкие цены", "широкий выбор"],
            "preferences":["ячневая крупа", "макароны", "щётки", "помидоры", "топлёное молоко", "противогриппозные средства", "елочные игрушки"],
            "fears":["дорого", "нет доставки"],
            "shopping_list":["макароны", "ячневая крупа", "помидоры", "елочные игрушки", "щётки", "топлёное молоко", "противогриппозные средства"],
            "budget_allocation":{"Крупы":0.35, "Бытовая химия":0.15, "Овощи":0.2, "Молочные продукты":0.1, "Лекарства":0.05, "Готовая еда":0.02, "Сезонные товары":0.1},
            "visit_time":56196.0
        },
        {
            "name":"Клиент_41", "age":30, "segment":"Молодые семьи с детьми",
            "motives":["качество продуктов для семьи", "удобство"],
            "preferences":["сливки", "топлёное молоко", "корм для детей", "картофель", "ячневая крупа", "противогриппозные средства"],
            "fears":["высокие цены", "мало ассортимента для детей"],
            "shopping_list":["картофель", "топлёное молоко", "ячневая крупа", "противогриппозные средства", "сливки"],
            "budget_allocation":{"Молочные продукты":0.2, "Детские товары":0.2, "Овощи":0.15, "Крупы":0.1, "Лекарства":0.05, "Готовая еда":0.01, "Сезонные товары":0.01, "Перекусы":0.01},
            "visit_time":51458.0
        },
        {
            "name":"Клиент_42", "age":43, "segment":"Люди из пригородов",
            "motives":["широкий выбор", "низкие цены"],
            "preferences":["гречка", "булгур", "пшено", "стиральный порошок", "чеснок", "капуста", "ряженка", "капли от насморка", "уголь"],
            "fears":["мало товара", "дорого"],
            "shopping_list":["гречка", "булгур", "уголь", "стиральный порошок", "пшено"],
            "budget_allocation":{"Крупы":0.35, "Бытовая химия":0.15, "Овощи":0.2, "Молочные продукты":0.1, "Лекарства":0.05, "Готовая еда":0.02, "Сезонные товары":0.1},
            "visit_time":41214.0
        },
        {
            "name":"Клиент_43", "age":43, "segment":"Люди из пригородов",
            "motives":["низкие цены", "широкий выбор"],
            "preferences":["пшено", "ячневая крупа", "чистящие средства", "чеснок", "сыр", "пластыри", "елочные игрушки"],
            "fears":["мало товара", "нет доставки"],
            "shopping_list":["пластыри", "елочные игрушки", "пшено", "чистящие средства", "чеснок", "ячневая крупа", "сыр"],
            "budget_allocation":{"Крупы":0.35, "Бытовая химия":0.15, "Овощи":0.2, "Молочные продукты":0.1, "Лекарства":0.05, "Готовая еда":0.02, "Сезонные товары":0.1},
            "visit_time":65369.0
        },
        {
            "name":"Клиент_44", "age":38, "segment":"Работающие люди",
            "motives":["доступность", "быстрота"],
            "preferences":["блины", "шаурма", "роллы", "орехи", "чипсы", "чай в бутылках", "сыр"],
            "fears":["очереди", "мало готовой еды"],
            "shopping_list":["чипсы", "чай в бутылках", "шаурма", "блины", "роллы", "орехи", "сыр"],
            "budget_allocation":{"Готовая еда":0.35, "Перекусы":0.25, "Энергетики":0.2, "Молочные продукты":0.05, "Овощи":0.01, "Сезонные товары":0.01, "Лекарства":0.01, "Крупы":0.01},
            "visit_time":38203.0
        },
        {
            "name":"Клиент_45", "age":32, "segment":"Работающие люди",
            "motives":["быстрота", "доступность"],
            "preferences":["пельмени", "готовые супы", "шаурма", "орехи", "газировка", "творог"],
            "fears":["неудобство", "очереди"],
            "shopping_list":["готовые супы", "шаурма", "пельмени", "орехи", "творог"],
            "budget_allocation":{"Готовая еда":0.35, "Перекусы":0.25, "Энергетики":0.2, "Молочные продукты":0.05, "Овощи":0.01, "Сезонные товары":0.01, "Лекарства":0.01, "Крупы":0.01},
            "visit_time":72264.0
        },
        {
            "name":"Клиент_46", "age":38, "segment":"Люди из пригородов",
            "motives":["низкие цены", "широкий выбор"],
            "preferences":["перловка", "макароны", "бумажные полотенца", "свёкла", "лук", "молоко", "бинты", "черешня"],
            "fears":["мало товара", "нет доставки"],
            "shopping_list":["молоко", "бумажные полотенца", "макароны", "бинты", "свёкла"],
            "budget_allocation":{"Крупы":0.35, "Бытовая химия":0.15, "Овощи":0.2, "Молочные продукты":0.1, "Лекарства":0.05, "Готовая еда":0.02, "Сезонные товары":0.1},
            "visit_time":51993.0
        },
        {
            "name":"Клиент_47", "age":26, "segment":"Работающие люди",
            "motives":["доступность", "готовые решения"],
            "preferences":["чебуреки", "пельмени", "роллы", "батончики", "чай в бутылках", "сливки"],
            "fears":["очереди", "мало готовой еды"],
            "shopping_list":["батончики", "чебуреки", "роллы", "чай в бутылках", "сливки", "пельмени"],
            "budget_allocation":{"Готовая еда":0.35, "Перекусы":0.25, "Энергетики":0.2, "Молочные продукты":0.05, "Овощи":0.01, "Сезонные товары":0.01, "Лекарства":0.01, "Крупы":0.01},
            "visit_time":54717.0
        },
        {
            "name":"Клиент_48", "age":56, "segment":"Люди из пригородов",
            "motives":["закуп впрок", "низкие цены"],
            "preferences":["ячневая крупа", "кускус", "моющее средство", "чеснок", "ряженка", "ибупрофен", "елочные игрушки"],
            "fears":["дорого", "нет доставки"],
            "shopping_list":["чеснок", "елочные игрушки", "кускус", "моющее средство", "ряженка", "ибупрофен", "ячневая крупа"],
            "budget_allocation":{"Крупы":0.35, "Бытовая химия":0.15, "Овощи":0.2, "Молочные продукты":0.1, "Лекарства":0.05, "Готовая еда":0.02, "Сезонные товары":0.1},
            "visit_time":42759.0
        },
        {
            "name":"Клиент_49", "age":67, "segment":"Пенсионеры",
            "motives":["всё в одном месте", "дешево"],
            "preferences":["перловка", "пшено", "творог", "кефир", "кабачки", "перец", "витамины"],
            "fears":["непонятные акции", "нет скидок"],
            "shopping_list":["витамины", "перец", "кабачки", "кефир", "пшено", "перловка"],
            "budget_allocation":{"Крупы":0.3, "Молочные продукты":0.25, "Овощи":0.2, "Лекарства":0.3, "Сезонные товары":0.01},
            "visit_time":44093.0
        },
        {
            "name":"Клиент_50", "age":37, "segment":"Люди из пригородов",
            "motives":["закуп впрок", "низкие цены"],
            "preferences":["булгур", "макароны", "кускус", "бумажные полотенца", "кабачки", "молоко", "капли от насморка", "новогодние украшения"],
            "fears":["дорого", "мало товара"],
            "shopping_list":["булгур", "бумажные полотенца", "кабачки", "кускус", "капли от насморка"],
            "budget_allocation":{"Крупы":0.35, "Бытовая химия":0.15, "Овощи":0.2, "Молочные продукты":0.1, "Лекарства":0.05, "Готовая еда":0.02, "Сезонные товары":0.1},
            "visit_time":62794.0
        }
    ]

    sim = StoreSimulation(store_data, max_queue_length=5, grid_width=20, grid_height=20)
    results = asyncio.run(sim.simulate_clients(clients))

    def convert_np(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    # Сохраняем финальный JSON в файл
    with open('simulation_results.json', 'w', encoding='utf-8') as out_file:
        json.dump(results, out_file, ensure_ascii=False, indent=2, default=convert_np)

    # Также выводим в консоль
    print(json.dumps(results, ensure_ascii=False, indent=2, default=convert_np))
