from typing import List
from fastapi import APIRouter, HTTPException, Query, Request, Response, status, Path
from fastapi.responses import JSONResponse
from app.models import Maps, Kasses
from app.dependencies import SessionDep
from app.schemas import kasses as kasses_schemas

router_kasses = APIRouter(prefix="/kasses", tags=["Кассы"])

@router_kasses.get(
    "",
    response_model=List[kasses_schemas.KassesOutput]
)
async def get_kassses(
    session: SessionDep,
    offset: int = 0,
    limit: int = 10,
):
    kasses = await Kasses.get_all(session, offset=offset, limit=limit)
    return kasses


@router_kasses.post(
    "",
    response_model=kasses_schemas.KassesOutput
)
async def create_kasses(
    session: SessionDep,
    payload: kasses_schemas.KassesCreate,
):
    kasses = await Kasses.create(session, payload)
    return kasses
    

@router_kasses.get(
    "/{kassa_id}",
    response_model=kasses_schemas.KassesOutput
)
async def get_kasses(
    session: SessionDep,
    kassa_id: int,
):
    kassa = await Kasses.get_by_id(session, kassa_id)
    if not kassa:
        raise HTTPException(status_code=404, detail="Касса не найдена")
    return kassa

@router_kasses.delete(
    "/{kassa_id}",
    status_code=204
)
async def delete_kassa(
    session: SessionDep,
    kassa_id: int,
):
    kassa = await Kasses.get_by_id(session, kassa_id)
    if not kassa:
        raise HTTPException(status_code=404, detail="Касса не найдена")
    await session.delete(kassa)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
