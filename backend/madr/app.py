import asyncio
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from madr.api.v1.router import routers
from madr.config import Settings
from madr.core.redis import lifespan as redis_lifespan
from madr.schemas import Message

settings = Settings()  # type: ignore


if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


app = FastAPI(lifespan=redis_lifespan)


@app.get('/', response_model=Message)
async def health():
    return {'message': 'ok'}


[app.include_router(router) for router in routers]
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
