from contextlib import asynccontextmanager

import ipdb  # noqa: F401
from fastapi import FastAPI
from redis.asyncio import ConnectionPool, Redis

from madr.settings import Settings

settings = Settings()  # type: ignore


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_pool = ConnectionPool.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        max_connections=10,
    )
    app.state.redis = Redis(connection_pool=redis_pool)

    yield

    await app.state.redis.close()
    await redis_pool.aclose()


def get_redis(request) -> Redis:
    return Redis(connection_pool=request.app.state.redis_pool)


async def get_user_token_version(redis: Redis, user_id: int) -> int:
    version = await redis.get(f'user:token_version:{user_id}')
    return int(version) if version else 0


async def invalidated_user_tokens(redis: Redis, user_id: int):
    """invalida todos os tokens antigos"""
    await redis.incr(f'user:token_version:{user_id}')
