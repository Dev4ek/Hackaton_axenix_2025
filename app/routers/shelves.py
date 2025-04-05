# routers/shelves.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.dependencies import SessionDep
from app.models import Shelves, Maps
from app.schemas import shelves as shelves_schemas

router_shelves = APIRouter(prefix="/shelves", tags=["Стеллажи"])

@router_shelves.post("", response_model=shelves_schemas.ShelfOutput)
async def create_shelf(
    session: SessionDep,
    payload: shelves_schemas.ShelfCreate
):
    # Проверим, есть ли карта
    map_obj = await Maps.get_by_id(session, payload.map_id)
    if not map_obj:
        raise HTTPException(status_code=404, detail="Карта не найдена")

    new_shelf = await Shelves.create(session, payload)
    return new_shelf


@router_shelves.get("", response_model=List[shelves_schemas.ShelfOutput])
async def get_shelves(
    session: SessionDep,
    offset: int = 0,
    limit: int = 10,
):
    shelves = await Shelves.get_all(session, offset=offset, limit=limit)
    return shelves


@router_shelves.get("/maps/{map_id}", response_model=List[shelves_schemas.ShelfProducts])
async def get_shelves_by_map(
    session: SessionDep,
    map_id: int
):
    shelves_list = await Shelves.get_by_map_id(session, map_id)
    return shelves_list

@router_shelves.get("/{shelf_id}", response_model=shelves_schemas.ShelfOutput)
async def get_shelf(
    session: SessionDep,
    shelf_id: int
):
    shelf = await Shelves.get_by_id(session, shelf_id)
    if not shelf:
        raise HTTPException(status_code=404, detail="Стеллаж не найден")
    return shelf


@router_shelves.delete("/{shelf_id}", status_code=204)
async def delete_shelf(
    session: SessionDep,
    shelf_id: int
):
    shelf = await Shelves.get_by_id(session, shelf_id)
    if not shelf:
        raise HTTPException(status_code=404, detail="Стеллаж не найден")

    await session.delete(shelf)
    await session.commit()
    return {}