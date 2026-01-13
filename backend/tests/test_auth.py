from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from unittest.mock import patch

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from madr.core.security import generate_token
from madr.models.user import User
from tests.utils import frozen_context

base_url_api = '/auth/token'


def test_users_deve_retornar_token_de_usuario_autenticado(
    client: TestClient, user: User
):
    payload = {
        'username': user.email,
        'password': '123456789',
    }
    response = client.post(base_url_api, data=payload)
    data = response.json()
    assert 'access_token' in data
    assert 'token_type' in data
    assert data['access_token'].startswith('ey')
    assert data['token_type'] == 'bearer'


def test_login_user_deve_falhar_senha_errada(client: TestClient, user: User):
    payload = {
        'username': user.email,
        'password': 'wrong_password_',
    }
    response = client.post(base_url_api, data=payload)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    data = response.json()
    assert data == {'detail': 'Incorrect username or password'}


def test_login_user_deve_falhar_user_nao_existe(
    client: TestClient, user: User
):
    payload = {
        'username': 'wrong_username_123',
        'password': '123456789',
    }
    response = client.post(base_url_api, data=payload)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    data = response.json()
    assert data == {'detail': 'Incorrect username or password'}


# @pytest.mark.asyncio
# async def test_login_atualiza_hash_quando_necessario(
#     client: TestClient, session: Session, user: User
# ):
#     password_plain = '123456789'

#     old_hash = user.password

#     # Mock authenticate_user diretamente para retornar needs_rehash=True
#     with patch('madr.api.v1.auth.authenticate_user') as mock_auth:
#         from madr.core.security import AuthResult  # noqa: PLC0415

#         # Retorna user com needs_rehash=True
#         mock_auth.return_value = AuthResult(
#             authenticated=True, user=user, needs_rehash=True
#         )

#         response = client.post(
#             base_url_api,
#             data={'username': user.username, 'password': password_plain},
#         )

#         assert response.status_code == HTTPStatus.OK


#         # Verificar que hash foi atualizado
#         await session.refresh(user)
#         assert user.password != old_hash
@pytest.mark.asyncio
async def test_login_atualiza_hash_quando_necessario(
    client: TestClient, session: Session, user: User
):
    password_plain = '123456789'

    from argon2 import PasswordHasher  # noqa: PLC0415

    ph = PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1)
    user.password = ph.hash(password_plain)
    await session.commit()

    old_hash = user.password
    user_id = user.id

    response = client.post(
        base_url_api,
        data={'username': user.username, 'password': password_plain},
    )

    assert response.status_code == HTTPStatus.OK

    session.expire_all()

    result = await session.execute(select(User).where(User.id == user_id))
    updated_user = result.scalar_one()

    assert updated_user.password != old_hash


@pytest.mark.asyncio
async def test_login_nao_atualiza_hash_quando_desnecessario(
    client: TestClient, session: Session, user: User
):
    password_plain = '123456789'

    old_hash = user.password

    with patch('madr.api.v1.auth.authenticate_user') as mock_auth:
        from madr.core.security import AuthResult  # noqa: PLC0415

        # Retorna user com needs_rehash=True
        mock_auth.return_value = AuthResult(
            authenticated=True, user=user, needs_rehash=False
        )

        response = client.post(
            base_url_api,
            data={'username': user.username, 'password': password_plain},
        )

        assert response.status_code == HTTPStatus.OK
        await session.refresh(user)
        assert user.password == old_hash


def test_generate_token_sem_exp_time_delta(user: User):
    data = {'sub': user.id, 'username': user.username, 'email': user.email}
    from madr.config import Settings  # noqa: PLC0415

    token = generate_token(data)
    settings = Settings()  # type: ignore

    decoded = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    exp = datetime.fromtimestamp(decoded['exp'], tz=timezone.utc)
    now = datetime.now(timezone.utc)

    assert decoded['sub'] == str(user.id)
    assert decoded['username'] == user.username
    assert timedelta(minutes=14) < (exp - now) < timedelta(minutes=16)


def test_generate_token_com_exp_time_delta(user: User):
    data = {'sub': user.id, 'username': user.username, 'email': user.email}
    from madr.config import Settings  # noqa: PLC0415

    settings = Settings()  # type: ignore
    expiration_token_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    custom_exp = timedelta(minutes=expiration_token_minutes)

    with frozen_context():
        now = datetime.now(timezone.utc)
        token = generate_token(data, custom_exp)

        decoded = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        expected_exp = int((now + custom_exp).timestamp())
        assert decoded['exp'] == expected_exp
