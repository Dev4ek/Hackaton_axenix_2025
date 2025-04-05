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
    ...
    
@router_simulations.post("/start")
async def start_simulation(
    session: SessionDep,
    payload: simulations_schemas.SimulationCreate
):
   ...