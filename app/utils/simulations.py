import math
import random
import select
from typing import List
from fastapi import APIRouter, HTTPException, Query, Request, Response, status, Path
from fastapi.responses import JSONResponse
from app.models import Maps, Products, Persons, PersonMovements, Sales
from app.dependencies import SessionDep
from app.schemas import simulations as simulations_schemas

async def get_heatmap(session, map_id: int):
    map_obj = await Maps.get_by_id(session, map_id)
    if not map_obj:
        return []

    movements = await PersonMovements.get_by_map_id(session, map_id)
    width = map_obj.x
    height = map_obj.z

    heat_counter = {}
    for move in movements:
        cx = int(move.x)
        cz = int(move.z)
        if 0 <= cx < width and 0 <= cz < height:
            heat_counter[(cx, cz)] = heat_counter.get((cx, cz), 0) + 1

    # Превратим словарь в список удобных JSON-объектов
    result = []
    for (cx, cz), count in heat_counter.items():
        result.append({
            "coords": [cx, cz],
            "count": count
        })

    return result

async def get_sales_stats(session, map_id: int):
    # 1) Общее количество продаж
    total_sales = await Sales.get_total_sales(session, map_id)

    # 2) Суммарная выручка
    total_revenue = await Sales.get_total_revenue(session, map_id)

    # 3) Группировка по продуктам
    product_sales = await Sales.get_sales_grouped_by_product(session, map_id)

    return {
        "total_sales_count": total_sales,
        "total_revenue": float(total_revenue),
        "by_product": product_sales
    }
