from typing import List
from fastapi import APIRouter, HTTPException, Query, Request, Response, status, Path
from fastapi.responses import JSONResponse
from app.models import Maps, Kasses, Categories, Shelves
from app.dependencies import SessionDep
from app.schemas import kasses as kasses_schemas
from app.schemas import categories as categories_schemas
from sqlalchemy.orm.attributes import flag_modified


router_categories = APIRouter(prefix="/categories", tags=["Категории"])
           

@router_categories.get(
    "",
    response_model=List[categories_schemas.CategoryesOutput]
)
async def get_categoriese(
    session: SessionDep,
):
    _Categories = await Categories.get_all(session)
    return _Categories


@router_categories.post(
    "/create",
    response_model=categories_schemas.CategoryesOutput
)
async def create_product(
    session: SessionDep,
    payload: categories_schemas.CreateCategoryProduct
):
    category = await Categories.get_by_name(session, payload.name)
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    category.products.append(payload.product_add)
    flag_modified(category, "products")  # явно указываем, что поле изменилось

    session.add(category)
    await session.commit()
    await session.refresh(category)  # перезагрузка состояния из базы
    return category

@router_categories.get(
    "/shevles/{shevle_id}",
    response_model=categories_schemas.CategoryesOutput
)
async def get_categoriese_by_shevles(
    session: SessionDep,
    shevle_id: int,
):
    shevel = await Shelves.get_by_id(session, shevle_id)
    
    _Categories = await Categories.get_by_name(session, shevel.category)
    if not _Categories:
        raise HTTPException(status_code=404, detail="Категории не найдены")
    return _Categories

