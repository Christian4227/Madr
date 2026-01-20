from datetime import timedelta
from typing import List
from uuid import uuid4

import factory
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer

from madr.app import app
from madr.core.database import get_session
from madr.core.security import generate_token, get_hash
from madr.models import table_registry
from madr.models.book import Book
from madr.models.novelist import Novelist
from madr.models.user import User
from madr.schemas.books import BookCreate
from madr.schemas.security import Token
from madr.schemas.user import UserCreate
from tests.factories import BookFactory, NovelistFactory, UserFactory

# @pytest.fixture(scope='session')
# def engine():
#     with PostgresContainer('postgres:17', driver='asyncpg') as postgres:
# _engine = create_async_engine(postgres.get_connection_url())
# yield _engine


@pytest.fixture(scope='session')
def engine():
    with PostgresContainer('postgres:17', driver='asyncpg') as postgres:
        _engine = create_async_engine(
            postgres.get_connection_url(),
            poolclass=NullPool,  # adicione isso
        )
        yield _engine


# @pytest_asyncio.fixture
# async def client(session: AsyncSession, user: User):

#     async def override_get_db():
#         yield session

#     async def override_get_current_user():
#         return user

#     app.dependency_overrides[get_session] = override_get_db
#     # app.dependency_overrides[get_current_user] = override_get_current_user

#     yield TestClient(app)

#     app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(session: AsyncSession, user: User):
    async def override_get_db():
        yield session

    app.dependency_overrides[get_session] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url='http://test'
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# @pytest_asyncio.fixture
# async def client(session: AsyncSession, user: User):
#     def override_get_db():
#         yield session

#     async def override_get_current_user():
#         return user  # ou UserPublic.from_orm(user)

#     app.dependency_overrides[get_session] = override_get_db
#     app.dependency_overrides[get_current_user] = override_get_current_user

#     yield TestClient(app)

#     app.dependency_overrides.clear()


# @pytest_asyncio.fixture
# async def client(session: AsyncSession, user: User):

#     def override_get_db():
#         yield session

#     async def override_active_user():
#         return user

#     app.dependency_overrides[get_session] = override_get_db
#     app.dependency_overrides[active_user] = override_active_user
# # type: ignore

#     yield TestClient(app=app)

#     app.dependency_overrides.clear()


# @pytest_asyncio.fixture
# async def client(session: AsyncSession):
#     from madr.core.database import get_session  # noqa: PLC0415

#     def override_get_db():
#         yield session

#     app.dependency_overrides[get_session] = override_get_db
#     yield TestClient(app=app)
#     app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def session(engine):
    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.drop_all)


@pytest_asyncio.fixture
async def user(session: AsyncSession):
    pwd_raw = '123456789'
    new_user = UserFactory()
    new_user.password = get_hash(pwd_raw)

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


@pytest_asyncio.fixture
async def novelist(session: AsyncSession):
    new_novelist = NovelistFactory.build()
    session.add(new_novelist)
    await session.commit()
    await session.refresh(new_novelist)
    return new_novelist


@pytest_asyncio.fixture
async def novelist_with_books(session: AsyncSession):
    async def _factory(
        qty: int = 1,
        name_prefix: str = 'book_name',
        title_prefix: str = 'book_title',
    ):
        novelist = NovelistFactory.build()
        session.add(novelist)
        await session.flush()
        await session.refresh(novelist)

        books = BookFactory.build_batch(
            size=qty,
            id_novelist=novelist.id,
            name=factory.Sequence(lambda n: f'{name_prefix}_{n}'),  # type: ignore
            title=factory.Sequence(lambda n: f'{title_prefix}_{n}'),  # type: ignore
        )
        session.add_all(books)
        await session.commit()

        return novelist

    return _factory


@pytest_asyncio.fixture
async def authenticated_token(user: User):
    token_delta_expire_time = timedelta(minutes=5)

    version = '0'
    # version = await get_user_token_version(redis_client, user_id)
    jti = uuid4()
    data = {
        'sub': user.id,
        'username': user.username,
        'email': user.email,
        'jti': str(jti),
        'ver': int(version),
    }
    access_token = generate_token(data, token_delta_expire_time)

    return Token(access_token=access_token, token_type='bearer')


@pytest_asyncio.fixture
async def users(session: AsyncSession):
    list_users: List[User] = []
    for n in range(11):
        new_user = User(
            username=f'alice_{n + 1}',
            password=get_hash(f'secret-{n + 1}'),
            email=f'teste{n + 1}@test',
        )
        session.add(new_user)
        list_users.append(new_user)
    await session.commit()
    return list_users


@pytest_asyncio.fixture
async def book(session: AsyncSession, novelist: Novelist) -> Book:
    book = BookFactory.build(id_novelist=novelist.id)
    session.add(book)
    await session.commit()
    await session.refresh(book)
    return book


@pytest_asyncio.fixture
async def book_payload(novelist: Novelist) -> dict:
    _book = BookFactory.build(id_novelist=novelist.id)
    book_validated = BookCreate.model_validate(_book, from_attributes=True)
    payload = book_validated.model_dump(by_alias=True)
    return payload


@pytest_asyncio.fixture
async def user_payload() -> dict:
    _user = UserFactory()
    user_validated = UserCreate.model_validate(_user, from_attributes=True)
    return user_validated.model_dump(by_alias=True)


@pytest_asyncio.fixture(autouse=True)
async def clear_overrides():
    yield
    app.dependency_overrides.clear()
