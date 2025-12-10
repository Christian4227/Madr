from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from madr.api.v1.router import routers
from madr.config import Settings

app = FastAPI()
settings = Settings()  # type: ignore


[app.include_router(router) for router in routers]
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
