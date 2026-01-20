# madr/types.py
from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from madr.core.database import get_session
from madr.core.redis import get_redis

T_redis = Annotated[Redis, Depends(get_redis)]
DBSession = Annotated[AsyncSession, Depends(get_session)]
