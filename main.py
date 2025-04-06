from dotenv import load_dotenv
load_dotenv()

from app import database
from app.fastapi_server import start_uvicorn
import asyncio
import os
import sys

async def main():
    database.create_tables()
    await start_uvicorn(),

if __name__ == "__main__":
    asyncio.run(main())

