import asyncio
import json
import math
import random
from typing import List
from fastapi import APIRouter, HTTPException, Query, Request, Response, status, Path
from fastapi.responses import JSONResponse
from app.models import Maps, Products, Persons, PersonMovements, Sales
from app.dependencies import SessionDep
from app.schemas import simulations as simulations_schemas
from app.schemas import persons as persons_schemas
from app.utils.simulations import main
import aiohttp

router_simulations = APIRouter(prefix="/simulations", tags=["Симуляции"])


@router_simulations.post("/start")
async def start_simulation(
    session: SessionDep,
    payload: simulations_schemas.SimulationCreate
):
    map = await Maps.get_by_id(session, payload.map_id)
    if not map:
        raise HTTPException(status_code=404, detail="Карта не найдена")
    
    json_data = None
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://localhost:8082/maps/{payload.map_id}/full") as response:
            # Проверяем, что запрос успешен (HTTP 200)
            if response.status == 200:
                json_data = await response.json()
            else:
                raise Exception(f"Ошибка запроса: {response.status}")
    if not json_data:
        raise HTTPException(status_code=500, detail="Ошибка получения информации о мапе json_data")
    
    json_data['kasses'] = json_data['kassses']
    results = await main(payload.num_persons, json_data)
    return json.loads(results)
    