from typing import List
from fastapi import APIRouter, HTTPException, Query, Request, Response, status, Path
from fastapi.responses import JSONResponse
from app.models import Maps, Persons
from app.dependencies import SessionDep
from app.schemas import maps as map_schemas

router_persons = APIRouter(prefix="/persons", tags=["Люди"])

@router_persons.get(
    "",
    response_model=List[map_schemas.MapOutput]
)
async def get_persons(
    session: SessionDep,
    offset: int = 0,
    limit: int = 10,
):
    persons = await Persons.get_all(session, offset=offset, limit=limit)
    return persons


@router_persons.post(
    "",
    response_model=
)