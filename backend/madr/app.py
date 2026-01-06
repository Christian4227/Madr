import asyncio
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from madr.api.v1.router import routers
from madr.config import Settings
from madr.schemas import Message

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI()
settings = Settings()  # type: ignore


@app.get('/', response_model=Message)
def health():
    return {'message': 'ok'}


[app.include_router(router) for router in routers]
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
