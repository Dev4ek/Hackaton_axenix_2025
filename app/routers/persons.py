from typing import List
from fastapi import APIRouter, HTTPException, Query, Request, Response, status, Path
from fastapi.responses import JSONResponse
from app.models import Maps, Persons
from app.dependencies import SessionDep
from app.schemas import persons as persons_schemas

router_persons = APIRouter(prefix="/persons", tags=["Люди"])

@router_persons.post(
    "",
    response_model=List[persons_schemas.PersonOutput]
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
    response_model=List[persons_schemas.PersonOutput]
)
async def create_person(
    session: SessionDep,
    payload_list: List[persons_schemas.PersonCreate],
):
    added_persons = []
    for payload in payload_list:
        person = await Persons.create(session, payload)
        added_persons.append(person)
        
    return added_persons

@router_persons.get(
    "/{person_id}",
    response_model=persons_schemas.PersonOutput
)
async def get_person(
    session: SessionDep,
    person_id: int,
):
    person = await Persons.get_by_id(session, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Люди не найдены")
    return person


@router_persons.get(
    "/maps/{map_id}",
    response_model=List[persons_schemas.PersonOutput]
)
async def get_persons_by_map(
    session: SessionDep,
    map_id: int,
):
    persons = await Persons.get_by_map_id(session, map_id)
    if not persons:
        raise HTTPException(status_code=404, detail="Люди не найдены")
    return persons

@router_persons.delete(
    "/{person_id}",
    status_code=204
)
async def delete_person(
    session: SessionDep,
    person_id: int,
):
    person = await Persons.get_by_id(session, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Люди не найдены")
    await session.delete(person)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)