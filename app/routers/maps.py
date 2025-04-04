from typing import List
from fastapi import APIRouter, HTTPException, Query, Request, Response, status, Path
from fastapi.responses import JSONResponse
from app.models import Maps
from app.dependencies import SessionDep
from app.schemas import maps as map_schemas

router_maps = APIRouter(prefix="/maps", tags=["Карты"])

@router_maps.get(
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


@router_maps.post(
    "",
    response_model=map_schemas.MapOutput
)
async def create_map(
    session: SessionDep,
    payload: map_schemas.MapCreate,
):
    maps = await Maps.create(session, payload)
    return maps
    

@router_maps.get(
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


@router_maps.delete(
    "/{map_id}",
    status_code=204
)
async def delete_map(
    session: SessionDep,
    map_id: int,
):
    map_ = await Maps.get_by_id(session, map_id)
    if not map_:
        raise HTTPException(status_code=404, detail="Карта не найдена")
    session.delete(map_)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)