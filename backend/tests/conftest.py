from datetime import timedelta
from typing import List

import pytest
from fastapi.testclient import TestClient
from pwdlib import PasswordHash
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from madr.app import app
from madr.core.security import Token, generate_token
from madr.models import table_registry
from madr.models.novelist import Novelist
from madr.models.user import User

pwd = PasswordHash.recommended()


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
    table_registry.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

    table_registry.metadata.drop_all(engine)
    engine.dispose()


def hash_password(raw_password: str) -> str:
    return pwd.hash(raw_password)


@pytest.fixture
def user(session: Session):
    hashed_password = hash_password('123456789')
    new_user = User(
        username='pedro', password=hashed_password, email='pedro@gmail.com'
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user


@pytest.fixture
def novelist(session: Session):
    new_novelist = Novelist(name='Hercule Poiroht')

    session.add(new_novelist)
    session.commit()
    session.refresh(new_novelist)
    return new_novelist


@pytest.fixture
def authenticated_header(user: User):
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
            password=hash_password(f'secret-{n + 1}'),
            email=f'teste{n + 1}@test',
        )
        session.add(new_user)
        list_users.append(new_user)
    session.commit()
    return list_users


# @pytest.fixture
# def books(session: Session):
#     list_users: List[User] = []
#     for n in range(11):
#         new_user = Book(


#             username=f'alice_{n + 1}',
#             password=f'secret-{n + 1}',
#             email=f'teste{n + 1}@test',
#         )
#         session.add(new_user)
#         list_users.append(new_user)
#     session.commit()
#     return list_users
