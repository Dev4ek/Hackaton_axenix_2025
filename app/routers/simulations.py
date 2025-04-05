import math
import random
from typing import List
from fastapi import APIRouter, HTTPException, Query, Request, Response, status, Path
from fastapi.responses import JSONResponse
from app.models import Maps, Products, Persons, PersonMovements, Sales
from app.dependencies import SessionDep
from app.schemas import simulations as simulations_schemas
from app.schemas import persons as persons_schemas
from app.utils import simulations as simulations_utils

router_simulations = APIRouter(prefix="/simulations", tags=["Симуляции"])

@router_simulations.get("/analysis/{map_id}")
async def get_analysis(
    session: SessionDep,
    map_id: int,
):
    # 1) Получаем "тепловую карту"
    heat_data = await simulations_utils.get_heatmap(session, map_id)
    
    # 2) Получаем продажи (общее и по товарам)
    sales_stats = await simulations_utils.get_sales_stats(session, map_id)

    # 3) Смотрим эффективность скидок
    discount_info = await Sales.get_discount_effectiveness(session, map_id)

    return {
        "heatmap": heat_data,
        "sales_stats": sales_stats,
        "discount_info": discount_info
    }
    
@router_simulations.post("/start")
async def start_simulation(
    session: SessionDep,
    payload: simulations_schemas.SimulationCreate
):
    """
    Запускает симуляцию на карте `map_id` с количеством покупателей `num_persons`.
    - Учитывается пиковое время (map_obj.time_peak_start / time_peak_end).
    - Моделируется логика очередей (если есть товар "Касса").
    - Генерируются случайные события (например, поломка кассы).
    - По итогам можно сделать GET /analysis/{map_id} для аналитики.
    """
    # 0. Настраиваем время симуляции (в секундах):
    # Например, 86400 = сутки, 21600 = 6 часов. 
    # Для демонстрации возьмём 36000 (10 часов).
    steps = 36000

    # 1. Получаем карту + время пиков
    map_obj = await Maps.get_by_id(session, payload.map_id)
    if not map_obj:
        raise ValueError(f"Карта {payload.map_id} не найдена.")
    peak_start = map_obj.time_peak_start  # сек (например, 43200 = 12:00)
    peak_end = map_obj.time_peak_end      # сек (например, 50400 = 14:00)

    # 2. Получаем список товаров (в т.ч. кассу и проч.)
    products = await Products.get_by_map_id(session, payload.map_id)
    if not products:
        raise ValueError(f"Нет товаров на карте {payload.map_id}")
    
    # Ищем товар, который является "Кассой" (по name или по типу).
    # Предположим, у нас есть product.name="Касса" - тогда мы можем моделировать очередь.
    cashier_product = None
    for prod in products:
        if prod.name.lower() == "касса":
            cashier_product = prod
            break

    # 3. Очищаем "старых" людей и создаём новых
    old_persons = await Persons.get_by_map_id(session, payload.map_id)
    for op in old_persons:
        await session.delete(op)
    await session.commit()

    persons_list = []
    for i in range(payload.num_persons):
        new_person = await Persons.create(
            session,
            persons_schemas.PersonCreate(map_id=payload.map_id)
        )
        persons_list.append(new_person)

    # 4. Начальные координаты и статусы
    person_positions = {p.id: [0.0, 0.0, 0.0] for p in persons_list}
    person_in_store = {p.id: True for p in persons_list}

    # Очередь (список ID людей, которые встали в очередь к кассе)
    queue_to_cashier = []

    # 5. Основной цикл: 1 шаг = 1 секунда
    for step in range(steps):
        # Проверяем, пиковое ли время (выше/ниже = 12:00..14:00)
        is_peak = (peak_start <= step <= peak_end)

        # Пример события: 0.01% шанс "поломки кассы" на каждом шаге
        # Если касса "ломается", то её нельзя использовать N шагов.
        # Можно хранить флаг cashier_broken_until = step + 1000 (пример).
        # Ниже - упрощённый пример.
        # (Раскомментируйте, если нужно)
        """
        if cashier_product and random.random() < 0.0001:
            # Считаем, что касса сломалась на 600 секунд (10 минут)
            cashier_product_broken_until = step + 600
        """

        for person in persons_list:
            if not person_in_store[person.id]:
                continue

            px, py, pz = person_positions[person.id]

            # Если человек уже стоит в очереди:
            if person.id in queue_to_cashier:
                # Допустим, обрабатываем 1 человека в 10 секунд (очередь).
                # Если мы на "голове" очереди, через 10 секунд — уходим.
                # Либо делаем более сложную логику.
                continue  # человек не перемещается, ждёт

            # === Проверяем, есть ли цель (товар) ===
            if person.target_product:
                # Находим нужный товар
                target_product = None
                for prod in products:
                    if prod.name == person.target_product:
                        target_product = prod
                        break

                if not target_product:
                    # сбрасываем цель
                    person.target_product = None
                    continue

                # Двигаемся
                tx, ty, tz = target_product.x, 0.7, target_product.z
                step_size = 0.2
                dx = tx - px
                dy = ty - py
                dz = tz - pz
                dist = (dx**2 + dy**2 + dz**2) ** 0.5

                if dist < 0.2:
                    # Дошли до товара => покупка
                    person_positions[person.id] = [tx, ty, tz]
                    movement = PersonMovements(
                        person_id=person.id,
                        map_id=payload.map_id,
                        x=tx, y=ty, z=tz
                    )
                    session.add(movement)

                    base_price = 100.0
                    price_final = base_price
                    if target_product.percent_discount:
                        price_final = base_price * (1 - target_product.percent_discount / 100)

                    sale = Sales(
                        person_id=person.id,
                        product_id=target_product.id,
                        map_id=payload.map_id,
                        price=price_final
                    )
                    session.add(sale)

                    # Сбрасываем цель
                    person.target_product = None

                    # После покупки человек решает идти к кассе (если касса есть)
                    if cashier_product:
                        # человек направляется к кассе
                        person.target_product = cashier_product.name
                else:
                    # Продолжаем движение
                    ratio = step_size / dist if dist != 0 else 0
                    px += dx * ratio
                    py += dy * ratio
                    pz += dz * ratio
                    person_positions[person.id] = [px, py, pz]

                    movement = PersonMovements(
                        person_id=person.id,
                        map_id=payload.map_id,
                        x=px, y=py, z=pz
                    )
                    session.add(movement)

            else:
                # Нет текущего товара => случайное поведение
                # Меняем вероятности с учётом пикового времени:
                if is_peak:
                    # В пик: 10% уйти, 50% взять товар, 40% прогулка
                    leave_threshold = 0.1
                    product_threshold = 0.6
                else:
                    # Вне пика: 20% уйти, 30% взять товар, 50% прогулка
                    leave_threshold = 0.2
                    product_threshold = 0.5

                roll = random.random()
                if roll < leave_threshold:
                    # Покидает магазин
                    person_in_store[person.id] = False
                    movement = PersonMovements(
                        person_id=person.id,
                        map_id=payload.map_id,
                        x=px, y=py, z=pz
                    )
                    session.add(movement)
                elif roll < product_threshold:
                    # Выбираем новый товар
                    new_target = random.choice(products)
                    person.target_product = new_target.name
                else:
                    # Прогулка
                    step_size = 0.2
                    angle = random.random() * 2 * math.pi
                    dx = step_size * math.cos(angle)
                    dz = step_size * math.sin(angle)
                    px += dx
                    pz += dz
                    person_positions[person.id] = [px, py, pz]

                    movement = PersonMovements(
                        person_id=person.id,
                        map_id=payload.map_id,
                        x=px, y=py, z=pz
                    )
                    session.add(movement)

            # === Проверяем, дошёл ли кто-то до кассы, чтобы встать в очередь ===
            if cashier_product and person.target_product == cashier_product.name:
                dist_to_cashier = (
                    (cashier_product.x - px)**2
                    + (0.7 - py)**2
                    + (cashier_product.z - pz)**2
                ) ** 0.5
                if dist_to_cashier < 0.2:
                    # Встаём в очередь
                    queue_to_cashier.append(person.id)
                    person.target_product = None  # сбрасываем цель

        # === Обслуживаем очередь ===
        # Допустим, 1 человек обслуживается 10 секунд
        # и уходит. Упрощённо: каждую секунду обслуживаем
        # "голову" очереди, если прошло 10 секунд с последнего ухода.
        # Здесь просто покажем идею.
        if len(queue_to_cashier) > 0:
            # Возьмём первого
            person_id_in_front = queue_to_cashier[0]
            # Уберём его из очереди с неким шансом или таймером:
            # Для примера, раз в 10 секунд
            if step % 10 == 0:
                queue_to_cashier.pop(0)
                # Человек уходит из магазина (или можно отправить его снова бродить)
                person_in_store[person_id_in_front] = False
                # Запишем последний movement
                ppx, ppy, ppz = person_positions[person_id_in_front]
                movement = PersonMovements(
                    person_id=person_id_in_front,
                    map_id=payload.map_id,
                    x=ppx, y=ppy, z=ppz
                )
                session.add(movement)

        # Сохраняем за этот шаг
        await session.commit()

    return {"success": True, "message": "Simulation completed."}