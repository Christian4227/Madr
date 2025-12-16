from datetime import timedelta
from typing import List

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from madr.app import app
from madr.core.security import generate_token, get_hash
from madr.models import table_registry
from madr.models.book import Book
from madr.models.novelist import Novelist
from madr.models.user import User
from madr.schemas.books import BookCreate
from madr.schemas.security import Token
from madr.schemas.user import UserCreate
from tests.factories import BookFactory, NovelistFactory, UserFactory


@pytest.fixture
def client(session: Session):
    from madr.core.database import get_session  # noqa: PLC0415

    def override_get_db():
        yield session

    app.dependency_overrides[get_session] = override_get_db
    yield TestClient(app=app)
    app.dependency_overrides.clear()  # type: ignore


@pytest.fixture
def session():
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )

    from sqlalchemy import event  # noqa: PLC0415

    @event.listens_for(engine, 'connect')
    def enabel_sqlite_fk(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()

    table_registry.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    table_registry.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def user(session: Session):
    pwd_raw = '123456789'
    new_user = UserFactory()
    new_user.password = get_hash(pwd_raw)

    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user


@pytest.fixture
def novelist(session: Session):
    new_novelist = NovelistFactory.build()
    session.add(new_novelist)
    session.commit()
    session.refresh(new_novelist)
    return new_novelist


@pytest.fixture
def novelist_with_books(session: Session):
    new_novelist = NovelistFactory.build()
    session.add(new_novelist)
    session.flush()

    books = BookFactory.build_batch(size=25, id_novelist=new_novelist.id)
    session.add_all(books)
    session.commit()
    session.refresh(new_novelist)
    return new_novelist


@pytest.fixture
def authenticated_token(user: User):
    token_delta_expire_time = timedelta(minutes=5)

    data = {'sub': user.id, 'username': user.username, 'email': user.email}

    access_token = generate_token(data, token_delta_expire_time)

    return Token(access_token=access_token, token_type='bearer')


@pytest.fixture
def users(session: Session):
    list_users: List[User] = []
    for n in range(11):
        new_user = User(
            username=f'alice_{n + 1}',
            password=get_hash(f'secret-{n + 1}'),
            email=f'teste{n + 1}@test',
        )
        session.add(new_user)
        list_users.append(new_user)
    session.commit()
    return list_users


@pytest.fixture
def book(session: Session, novelist: Novelist) -> Book:
    book = BookFactory.build(id_novelist=novelist.id)
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


@pytest.fixture
def book_payload(novelist: Novelist) -> dict:
    _book = BookFactory.build(id_novelist=novelist.id)
    book_validated = BookCreate.model_validate(_book, from_attributes=True)
    payload = book_validated.model_dump(by_alias=True)
    return payload


@pytest.fixture
def user_payload() -> dict:
    _user = UserFactory()
    user_validated = UserCreate.model_validate(_user, from_attributes=True)

    return user_validated.model_dump(by_alias=True)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()
