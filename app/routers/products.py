from typing import List
from fastapi import APIRouter, HTTPException, Query, Request, Response, status, Path
from fastapi.responses import JSONResponse
from app.models import Maps, Products
from app.dependencies import SessionDep
from app.schemas import products as products_schemas

router_products = APIRouter(prefix="/products", tags=["Продукты"])

@router_products.get(
    "",
    response_model=List[products_schemas.ProductOutput]
)
async def get_all(
    session: SessionDep,
    offset: int = 0,
    limit: int = 10,
):
    maps = await Products.get_all(session, offset=offset, limit=limit)
    return maps


@router_products.post(
    "",
    response_model=products_schemas.ProductOutput
)
async def create_product(
    session: SessionDep,
    payload: products_schemas.ProductCreate,
):
    new_product = await Products.create(session, payload)
    return new_product


@router_products.get(
    "/{product_id}",
    response_model=products_schemas.ProductOutput
)
async def get_product(
    session: SessionDep,
    product_id: int,
):
    product = await Products.get_by_id(session, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    return product

@router_products.get(
    "/maps/{map_id}",
    response_model=List[products_schemas.ProductOutput]
)
async def get_products_by_map(
    session: SessionDep,
    map_id: int,
):
    products = await Products.get_by_map_id(session, map_id)
    if not products:
        raise HTTPException(status_code=404, detail="Продукты не найдены")
    return products


