from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from madr.config import Settings

engine = create_async_engine(
    Settings().DATABASE_URL,  # type: ignore
    echo=False,
    pool_pre_ping=True,
)
async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session():  # pragma: no cover
    async with async_session() as session:
        yield session
