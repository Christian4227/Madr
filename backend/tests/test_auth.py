from http import HTTPStatus
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from madr.models.user import User

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


def test_user_deve_falhar_na_autenticacao(client: TestClient, user: User):
    payload = {
        'username': user.email,
        'password': 'wrong_password_',
    }
    response = client.post(base_url_api, data=payload)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    data = response.json()
    assert data == {'detail': 'Incorrect username or password'}


def test_login_atualiza_hash_quando_necessario(
    client: TestClient, session: Session, user: User
):
    password_plain = '123456789'

    old_hash = user.password

    # Mock authenticate_user diretamente para retornar needs_rehash=True
    with patch('madr.api.v1.auth.authenticate_user') as mock_auth:
        from madr.core.security import AuthResult  # noqa: PLC0415

        # Retorna user com needs_rehash=True
        mock_auth.return_value = AuthResult(
            authenticated=True, user=user, needs_rehash=True
        )

        response = client.post(
            base_url_api,
            data={'username': user.username, 'password': password_plain},
        )

        assert response.status_code == HTTPStatus.OK

        # Verificar que hash foi atualizado
        session.refresh(user)
        assert user.password != old_hash


def test_login_nao_atualiza_hash_quando_desnecessario(
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
        session.refresh(user)
        assert user.password == old_hash
