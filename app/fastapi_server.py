import traceback
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.config import settings
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles

from app.routers import router_maps, router_products,  router_simulations, router_shelves, router_kasses

app = FastAPI(
    title="Hackaton",
    version="1.0.0",
    docs_url='/docs',
    openapi_url='/openapi.json',
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_credentials=True,
    allow_headers=["*"]
)

# app.mount("/static", StaticFiles(directory="static"), name="static")

# Включение роутеров
app.include_router(router_maps)
app.include_router(router_shelves)
app.include_router(router_products)
app.include_router(router_kasses)
app.include_router(router_simulations)

# Обработка исключений
@app.exception_handler(StarletteHTTPException)
async def starlette_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

def custom_openapi():
    http_bearer = HTTPBearer()
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Hackaton",
        version="1.0.0",
        routes=app.routes,
    )

    # Добавляем Bearer токен в securitySchemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    # Указываем, что все запросы защищены Bearer токеном
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Асинхронный запуск Uvicorn-сервера
async def start_uvicorn():
    config = uvicorn.Config(app, host=settings.HOST, port=8082, workers=settings.WORKERS)
    server = uvicorn.Server(config)
    await server.serve()

