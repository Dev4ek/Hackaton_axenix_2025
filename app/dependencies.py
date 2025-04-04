import json
from typing import Annotated, Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app import database
import jwt
from app.config import settings

SessionDep = Annotated[AsyncSession, Depends(database.get_session)]
