from typing import List
from fastapi import APIRouter, HTTPException, Query, Request, Response, status, Path
from fastapi.responses import JSONResponse
from app.models import Maps
from app.dependencies import SessionDep
from app.schemas import map as map_schemas

router_map = APIRouter(prefix="/schemas", tags=["Карты"])

@router_map.get(
    "",
    response_model=List[map_schemas.MapOutput]
)
async def get_maps(
    session: SessionDep,
    offset: int = 0,
    limit: int = 10,
):
    maps = await Maps.get_all(session, offset=offset, limit=limit)
    return maps


@router_map.post(
    "",
    response_model=map_schemas.MapOutput
)
async def create_map(
    session: SessionDep,
    payload: map_schemas.MapCreate,
):
    maps = await Maps.create(session, payload.name)
    return maps
    

@router_map.get(
    "/{map_id}",
    response_model=map_schemas.MapOutput
)
async def get_map(
    session: SessionDep,
    map_id: int,
):
    map_ = await Maps.get_by_id(session, map_id)
    if not map_:
        raise HTTPException(status_code=404, detail="Карта не найдена")
    return map_
