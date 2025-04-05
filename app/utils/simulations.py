import asyncio
import numpy as np
import random
import json
from collections import deque, defaultdict

###############################
#   CONSTANTS AND UTILITIES   #
###############################

BLOCK_TIME_SECONDS = 0.6                 # базовое время перемещения по клетке (сек)
OPEN_TIME_SECONDS = 8 * 3600           # время открытия: 8:00 (в секундах от полуночи, 28800)
CLOSE_TIME_SECONDS = 20 * 3600         # время закрытия: 20:00 (72000)
QUEUE_SERVICE_TIME = 10                # обслуживание очереди: 10 сек на клиента
MAX_QUEUE_LENGTH_DEFAULT = 5           # максимальная длина очереди
BASE_PURCHASE_CHANCE = 0.2             # базовая вероятность покупки
MOTIVE_BONUS = 0.3                     # бонус, если активен мотив "дешево"
FEAR_PENALTY = 0.3                     # штраф, если активен страх ("нет скидок")
DISCOUNT_BONUS = 0.1                   # бонус за скидку (каждые 10% – прибавка)
MIN_CHANCE_TO_APPROACH = 0.3           # минимальный шанс, чтобы клиент подошёл к полке
PREFERENCE_BONUS = 0.1                 # бонус, если товар входит в список предпочтений клиента
BUDGET_BONUS_FACTOR = 0.2              # коэффициент бонуса от распределения бюджета
KASSA_BREAK_PROB = 0.01                # вероятность поломки кассы (1%)

###############################
#   BFS: КРАТЧАЙШИЙ МАРШРУТ   #
###############################
def bfs_path(grid_width, grid_height, start, end, occupied_positions):
    """
    Ищем кратчайший путь от start до end (включая обе точки) на сетке grid_width x grid_height.
    Разрешается вход в конечную клетку, даже если она занята.
    Возвращаем список координат [(x, z), ...] или None.
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
        for dx, dz in [(1,0), (-1,0), (0,1), (0,-1)]:
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
    return abs(p1[0]-p2[0]) + abs(p1[1]-p2[1])

###############################
#   STEP-BY-STEP MOVEMENT     #
###############################
def move_along_path(path_cells, current_time, current_occupied, cell_visits,
                    block_time=BLOCK_TIME_SECONDS, close_time=CLOSE_TIME_SECONDS):
    """
    Перемещаемся по клеткам из path_cells, освобождая предыдущую клетку и занимая новую.
    Возвращает (конечную позицию, обновлённое время, статус) и лог перемещений.
    status может быть 'ok' или 'store_closed', если время вышло.
    """
    path_log = []
    position = path_cells[0]
    current_occupied.add(position)
    path_log.append({"x": position[0], "z": position[1], "time": current_time})
    cell_visits[position] += 1

    status = 'ok'
    for cell in path_cells[1:]:
        current_occupied.remove(position)
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
        Симуляция движения по магазину:
         - Перемещение по клеткам (move_along_path)
         - Учитываются занятые клетки (полки, кассы)
         - Клиенты проходят последовательно
        """
        self.store_schema = store_schema
        self.shelves, self.kasses, self.item_map = self.load_store(store_schema)

        self.grid_width = grid_width
        self.grid_height = grid_height
        self.max_queue_length = max_queue_length

        # Каждая касса имеет свою очередь
        self.queues = [[] for _ in self.kasses]

        # Занятые позиции для полок и касс
        self.base_occupied_positions = set()
        for shelf in store_schema['shelves']:
            self.base_occupied_positions.add((shelf['x'], shelf['z']))
        for kassa in store_schema['kasses']:
            self.base_occupied_positions.add((kassa['x'], kassa['z']))

        self.cell_visits = defaultdict(int)
        self.global_stats = {
            "total_purchases": 0,
            "motive_trigger_count": 0,
            "fear_trigger_count": 0,
            "discount_trigger_count": 0,
            "kassa_breakdowns": 0
        }
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

    def compute_purchase_chance(self, client, cat, product_info):
        chance = BASE_PURCHASE_CHANCE
        triggered_motive = False
        triggered_fear = False
        triggered_discount = False

        # Мотив "дешево"
        if any("дешево" in m.lower() for m in client.get('motives', [])):
            disc = product_info.get('percent_discount')
            if disc and disc > 0:
                chance += MOTIVE_BONUS
                triggered_motive = True

        # Страх "нет скидок"
        if any("нет скидок" in f.lower() for f in client.get('fears', [])):
            disc = product_info.get('percent_discount')
            if not disc or disc == 0:
                chance -= FEAR_PENALTY
                triggered_fear = True

        # Скидка
        disc = product_info.get('percent_discount')
        if disc and disc > 0:
            triggered_discount = True
            chance += (disc / 10.0) * DISCOUNT_BONUS

        # Бонус, если товар входит в предпочтения
        preferences = [p.lower() for p in client.get('preferences', [])]
        if product_info.get('name') and product_info["name"].lower() in preferences:
            chance += PREFERENCE_BONUS

        # Бюджетное распределение: если категория (полки) присутствует в budget_allocation,
        # добавляем бонус, пропорциональный выделенной сумме
        allocation_bonus = client.get('budget_allocation', {}).get(cat, 0) * BUDGET_BONUS_FACTOR
        chance += allocation_bonus

        if triggered_motive:
            self.global_stats["motive_trigger_count"] += 1
        if triggered_fear:
            self.global_stats["fear_trigger_count"] += 1
        if triggered_discount:
            self.global_stats["discount_trigger_count"] += 1

        chance = max(0.0, min(1.0, chance))
        return chance

    async def simulate_client(self, client, start_position=(0, 0), start_time=OPEN_TIME_SECONDS):
        """
        Симуляция движения клиента по магазину:
         1. Клиент входит в магазин в момент start_time.
         2. Для каждого товара из shopping_list, если шанс покупки достаточный, идёт к соответствующей полке.
         3. После обхода полок клиент идёт к кассе.
        """
        current_time = start_time
        status = "completed"
        path_log = []
        purchases_log = []
        position = start_position

        # Если стартовая позиция занята, подбираем альтернативную по оси X
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

        self.current_occupied.add(position)
        path_log.append({"x": position[0], "z": position[1], "time": current_time, "event": "entered_store"})
        self.cell_visits[position] += 1

        for item in client.get('shopping_list', []):
            if current_time > CLOSE_TIME_SECONDS:
                status = "store_closed"
                break

            item_lower = item.lower()
            if item_lower not in self.item_map:
                continue

            # Получаем категорию, позицию полки и информацию о товаре
            cat, shelf_pos, product_info = self.item_map[item_lower]
            # Вычисляем шанс покупки с учетом бюджета для категории
            chance = self.compute_purchase_chance(client, cat, product_info)
            if chance < MIN_CHANCE_TO_APPROACH:
                continue

            path_cells = bfs_path(self.grid_width, self.grid_height, position, shelf_pos, self.current_occupied)
            if not path_cells:
                status = "no_path_to_shelf"
                break

            final_pos, new_time, st, move_log = move_along_path(
                path_cells, current_time, self.current_occupied, self.cell_visits
            )
            if len(move_log) > 1:
                path_log.extend(move_log[1:])

            position = final_pos
            current_time = new_time

            if st == 'store_closed' or current_time > CLOSE_TIME_SECONDS:
                status = "store_closed"
                break

            path_log[-1]["event"] = f"arrived_shelf ({cat})"

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

            if purchased:
                self.global_stats["total_purchases"] += 1
                path_log[-1]["purchase_item"] = item
                path_log[-1]["purchase_chance"] = round(chance, 3)
                path_log[-1]["event"] += f"; PURCHASED: {item}"
            else:
                path_log[-1]["purchase_item"] = item
                path_log[-1]["purchase_chance"] = round(chance, 3)
                path_log[-1]["event"] += f"; DID_NOT_BUY: {item}"

        # После обхода полок идём к кассе, если клиент еще в магазине
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
                # Симуляция небольшой вероятности поломки кассы
                if random.random() < KASSA_BREAK_PROB:
                    self.global_stats["kassa_breakdowns"] += 1
                    status = "kassa_broken"
                    path_log.append({
                        "x": position[0],
                        "z": position[1],
                        "time": current_time,
                        "event": "kassa_broken"
                    })
                    return {
                        "client": client['name'],
                        "path": path_log,
                        "purchases": purchases_log,
                        "end_time": current_time,
                        "status": status
                    }
                if len(self.queues[chosen_kassa]) >= self.max_queue_length:
                    status = "left_due_to_queue"
                else:
                    kassa_pos = self.kasses[chosen_kassa]
                    path_cells = bfs_path(self.grid_width, self.grid_height, position, kassa_pos, self.current_occupied)
                    if not path_cells:
                        status = "no_path_to_kassa"
                    else:
                        final_pos, new_time, st, move_log = move_along_path(
                            path_cells, current_time, self.current_occupied, self.cell_visits
                        )
                        if len(move_log) > 1:
                            path_log.extend(move_log[1:])
                        position = final_pos
                        current_time = new_time

                        if st == 'store_closed' or current_time > CLOSE_TIME_SECONDS:
                            status = "store_closed"
                        else:
                            self.queues[chosen_kassa].append(client['name'])
                            queue_wait_time = len(self.queues[chosen_kassa]) * QUEUE_SERVICE_TIME
                            current_time += queue_wait_time
                            path_log.append({
                                "x": position[0],
                                "z": position[1],
                                "time": current_time,
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
        self.current_occupied = set(self.base_occupied_positions)
        total_clients = len(clients)
        # 60% клиентов приходят в пиковый период (12:00–14:00)
        num_peak = int(total_clients * 0.4)
        random.shuffle(clients)
        peak_clients = clients[:num_peak]
        non_peak_clients = clients[num_peak:]
        
        peak_start = 12 * 3600  # 43200
        peak_end = 14 * 3600    # 50400
        for client in peak_clients:
            client.update({'arrival_time':random.uniform(peak_start, peak_end)})
        
        open_time = OPEN_TIME_SECONDS  # 28800
        close_time = CLOSE_TIME_SECONDS  # 72000
        non_peak_interval = (peak_start - open_time) + (close_time - peak_end)
        for client in non_peak_clients:
            r = random.uniform(0, non_peak_interval)
            if r < (peak_start - open_time):
                client['arrival_time'] = open_time + r
            else:
                client['arrival_time'] = peak_end + (r - (peak_start - open_time))
        
        clients.sort(key=lambda c: c['arrival_time'])
        results = []
        global_time = OPEN_TIME_SECONDS
        for client in clients:
            if client['arrival_time'] > global_time:
                global_time = client['arrival_time']
            result = await self.simulate_client(client, start_time=global_time)
            results.append(result)
            # Сброс очередей и состояния занятых клеток для следующего клиента
            self.queues = [[] for _ in self.kasses]
            self.current_occupied = set(self.base_occupied_positions)
            global_time = result['end_time']
        
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
            "discount_trigger_count": self.global_stats["discount_trigger_count"],
            "kassa_breakdowns": self.global_stats["kassa_breakdowns"]
        }

        popular_zones = sorted(
            [{"x": k[0], "z": k[1], "visits": v} for k, v in self.cell_visits.items()],
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
async def main(count,store_data):
    import sys
    from .test import CustomerGenerator
    random.seed(42)

    # Здесь полный список из 50 клиентов
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

    return json.dumps(results, ensure_ascii=False, indent=2, default=convert_np)
if __name__ == '__main__':
    with open('/home/milaha/Документы/Hackaton_axenix_2025/app/utils/kassas_updated.json', encoding='utf-8') as f:
        store_data = json.load(f)
    asyncio.run(main(5000,store_data))
