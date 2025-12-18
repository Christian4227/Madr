import secrets
from datetime import timedelta
from http import HTTPStatus
from unittest.mock import Mock

import ipdb  # noqa: F401
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from madr.api.v1.users import create_user
from madr.app import app
from madr.core.database import get_session
from madr.models.user import User
from madr.schemas.security import Token
from madr.schemas.user import UserCreate, UserUpdate
from tests.utils import frozen_context

base_url = '/users/'


def test_users_deve_retornar_usuario_criado_com_id(client: TestClient):
    payload = {
        'username': 'pedrinho',
        'email': 'pedrinho@gmail.com.br',
        'password': 'batatinhas',
    }
    response = client.post(
        base_url,
        json=payload,
    )
    del payload['password']
    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {**payload, 'id': 1}


def test_users_deve_retornar_excessao_conflito_409(
    client: TestClient, user: User
):
    user_schema = UserCreate.model_validate(user, from_attributes=True)

    payload = user_schema.model_dump()
    payload['password'] = '123456789'
    response = client.post(
        base_url,
        json=payload,
    )

    assert response.status_code == HTTPStatus.CONFLICT

    assert response.json() == {'detail': 'User already exists'}


def test_delete_user_deve_retornar_success_delecao(
    client: TestClient, authenticated_token: Token
):
    response = client.delete(
        base_url,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Account Removed'}


def test_update_user_deve_retornar_user_modificado(
    client: TestClient, user: User, authenticated_token: Token
):
    username = user.username
    modified_username = f'modified_{username}'

    payload = {
        'username': modified_username,
    }

    response = client.put(
        base_url,
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    data = response.json()
    assert data['username'] == modified_username


def test_update_user_nao_deve_atualizar_password(
    client: TestClient,
    user: User,
    authenticated_token: Token,
    session: Session,
):
    original_password = user.password
    new_pwd = secrets.token_urlsafe(15)
    payload = {
        'username': 'novo_username',
        'pasword': new_pwd,
    }

    response = client.put(
        base_url,
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert data['username'] == 'novo_username'
    session.refresh(user)
    assert user.password == original_password


def test_create_user_nao_grava_no_db_em_caso_de_erro(
    user_payload: dict, session: Session
):
    mock_session = Mock(spec=Session)
    mock_session.commit.side_effect = IntegrityError(
        'statement', 'params', Exception('unique constraint failed')
    )

    def mock_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = mock_get_session

    client = TestClient(app=app)
    response = client.post(base_url, json=user_payload)

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'User already exists'}
    mock_session.rollback.assert_called_once()

    stmt = select(User).where(User.username == user_payload['username'])
    user = session.scalar(stmt)

    assert user is None


def test_create_user_deve_falhar_com_rollback(user_payload: dict):
    mock_session = Mock(spec=Session)

    mock_session.commit.side_effect = IntegrityError(
        'statement', 'params', Exception('unique constraint failed')
    )

    def mock_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = mock_get_session

    client = TestClient(app=app)
    response = client.post(base_url, json=user_payload)

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'User already exists'}
    mock_session.rollback.assert_called_once()


def test_create_user_deve_falhar_com_rollback_conflict(user_payload: dict):
    mock_session = Mock(spec=Session)

    mock_session.commit.side_effect = IntegrityError(
        'statement', 'params', Exception('unique constraint')
    )

    # Converte dict em objeto Pydantic
    user_create = UserCreate(**user_payload)

    with pytest.raises(HTTPException) as exc_info:
        create_user(user_create, mock_session)

    assert exc_info.value.status_code == HTTPStatus.CONFLICT

    assert exc_info.value.detail == 'User already exists'

    mock_session.rollback.assert_called_once()


@pytest.mark.parametrize(
    'field_missing',
    ['username', 'email', 'password'],
)
def test_create_user_deve_falhar_sem_campos_obrigatorios(
    client: TestClient,
    field_missing: str,
    session: Session,
    user_payload: dict,
):
    del user_payload[field_missing]

    response = client.post(
        base_url,
        json=user_payload,
    )
    data = response.json()
    for detail in data['detail']:
        if detail['type'] == 'missing':
            assert field_missing == detail['loc'][1]

    user = session.scalars(select(User)).one_or_none()
    # ipdb.set_trace()
    assert user is None

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_update_user_deve_falhar_com_rollback(
    user_payload: dict,
    session: Session,
    authenticated_token: Token,
    user: User,
):

    del user_payload['password']

    original_validated = UserUpdate.model_validate(user, from_attributes=True)
    original_user = original_validated.model_dump(exclude_unset=True)

    mock_session = Mock()
    mock_session.scalar.return_value = user
    mock_session.commit.side_effect = SQLAlchemyError('Database error')
    mock_session.rollback = Mock()

    # sessão que falha e lança exceção
    def mock_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = mock_get_session
    client = TestClient(app=app)

    response = client.put(
        base_url,
        json=user_payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {'detail': 'Failed to update user'}
    mock_session.rollback.assert_called_once()
    session.refresh(user)
    for key, value in user_payload.items():
        assert original_user[key] != value


def test_delete_user_deve_falhar_com_rollback(
    session: Session, client: TestClient, authenticated_token: Token
):
    mock_session = Mock()

    mock_session.commit.side_effect = SQLAlchemyError('DB Error')
    mock_session.rollback = Mock()

    # sessão que falha e lança exceção
    def mock_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = mock_get_session
    client = TestClient(app=app)

    response = client.delete(
        base_url,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {
        'detail': 'Cannot delete account with existing references'
    }
    mock_session.rollback.assert_called_once()
    user_db = session.execute(select(User)).one_or_none()
    assert user_db


def test_delete_user_deve_falhar_token_expirado(
    session: Session, client: TestClient, authenticated_token: Token
):
    with frozen_context(timedelta(minutes=31)):
        response = client.delete(
            base_url,
            headers={
                'Authorization': f'Bearer {authenticated_token.access_token}'
            },
        )
        users = session.scalars(select(User)).all()

        assert len(users) == 1
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json() == {'detail': 'Expired token'}


def test_update_user_deve_falhar_token_expirado(
    session: Session,
    client: TestClient,
    user: User,
    authenticated_token: Token,
):

    username = user.username
    modified_username = f'modified_{username}'

    payload = {
        'username': modified_username,
    }
    with frozen_context(timedelta(minutes=31)):
        response = client.put(
            base_url,
            json=payload,
            headers={
                'Authorization': f'Bearer {authenticated_token.access_token}'
            },
        )
        stmt = select(User).where(User.username == modified_username)
        user_modified = session.scalar(stmt)

        assert user_modified is None

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json() == {'detail': 'Expired token'}


def test_create_user_conflict_unique_violation(user_payload: dict):
    """Testa CONFLICT quando é violação de unicidade"""
    mock_session = Mock(spec=Session)
    mock_session.commit.side_effect = IntegrityError(
        'statement', 'params', Exception('unique constraint')
    )

    def mock_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = mock_get_session

    client = TestClient(app=app)
    response = client.post(base_url, json=user_payload)

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'User already exists'}
    mock_session.rollback.assert_called_once()


def test_create_user_database_error_generic(user_payload: dict, monkeypatch):
    """Testa 500 quando NÃO é violação de unicidade"""
    mock_session = Mock(spec=Session)
    mock_session.commit.side_effect = IntegrityError(
        'statement', 'params', Exception('foreign key violation')
    )

    # Força is_unique_violation retornar False
    monkeypatch.setattr(
        'madr.api.v1.users.is_unique_violation', lambda x: False
    )

    def mock_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = mock_get_session

    client = TestClient(app=app)
    response = client.post(base_url, json=user_payload)

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {'detail': 'Database error'}
    mock_session.rollback.assert_called_once()
