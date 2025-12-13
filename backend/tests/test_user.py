import secrets
from http import HTTPStatus
from unittest.mock import Mock

import ipdb  # noqa: F401
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from madr.app import app
from madr.core.database import get_session
from madr.models.user import User
from madr.schemas.security import Token
from madr.schemas.user import UserCreate, UserUpdate
from tests.factories import UserFactory

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

    assert response.json() == {'detail': 'User has been exists'}


def test_update_user_deve_retornar_success_delecao(
    client: TestClient, authenticated_header: Token
):
    response = client.delete(
        base_url,
        headers={
            'Authorization': f'Bearer {authenticated_header.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Account Removed'}


def test_update_user_deve_retornar_user_modificado(
    client: TestClient, user: User, authenticated_header: Token
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
            'Authorization': f'Bearer {authenticated_header.access_token}'
        },
    )

    data = response.json()

    assert data['username'] == modified_username


def test_update_user_nao_deve_atualizar_password(
    client: TestClient,
    user: User,
    authenticated_header: Token,
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
            'Authorization': f'Bearer {authenticated_header.access_token}'
        },
    )

    data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert data['username'] == 'novo_username'
    session.refresh(user)
    assert user.password == original_password


def test_create_user_deve_falhar_com_rollback(session: Session):

    fake_user_data = UserFactory()
    fake_user_data_validated = UserCreate.model_validate(
        fake_user_data, from_attributes=True
    )
    user_data_to_create = fake_user_data_validated.model_dump()
    mock_session = Mock()

    mock_session.scalar.return_value = None
    mock_session.commit.side_effect = SQLAlchemyError('DB Error')
    mock_session.rollback = Mock()

    # sessão que falha e lança exceção
    def mock_get_session():
        yield mock_session

    try:
        app.dependency_overrides[get_session] = mock_get_session
        client = TestClient(app=app)

        response = client.post(base_url, json=user_data_to_create)

        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert response.json() == {'detail': 'Failed to create user'}
        mock_session.rollback.assert_called_once()
        user_db = session.scalar(
            select(User).where(
                User.username == user_data_to_create['username']
            )
        )
        assert user_db is None
    finally:
        app.dependency_overrides.clear()


def test_update_user_deve_falhar_com_rollback(
    session: Session,
    authenticated_header: Token,
    user: User,
):

    from madr.app import app  # noqa: PLC0415
    from madr.core.database import get_session  # noqa: PLC0415

    fake_user_data = UserFactory()
    fake_user_data_validated = UserUpdate.model_validate(
        fake_user_data, from_attributes=True
    )
    user_data_to_update = fake_user_data_validated.model_dump(
        exclude={
            'password',
        }
    )

    original_validated = UserUpdate.model_validate(user, from_attributes=True)
    original_user = original_validated.model_dump(exclude_unset=True)

    mock_session = Mock()
    mock_session.scalar.return_value = user
    mock_session.commit.side_effect = SQLAlchemyError('DB Error')
    mock_session.rollback = Mock()

    # sessão que falha e lança exceção
    def mock_get_session():
        yield mock_session

    try:
        app.dependency_overrides[get_session] = mock_get_session
        client = TestClient(app=app)

        response = client.put(
            base_url,
            json=user_data_to_update,
            headers={
                'Authorization': f'Bearer {authenticated_header.access_token}'
            },
        )

        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert response.json() == {'detail': 'Failed to update user'}
        mock_session.rollback.assert_called_once()
        session.refresh(user)
        for key, value in user_data_to_update.items():
            assert original_user[key] != value
    finally:
        app.dependency_overrides.clear()


def test_delete_user_deve_falhar_com_rollback(
    session: Session, client: TestClient, authenticated_header: Token
):
    mock_session = Mock()

    mock_session.commit.side_effect = SQLAlchemyError('DB Error')
    mock_session.rollback = Mock()

    # sessão que falha e lança exceção
    def mock_get_session():
        yield mock_session

    try:
        app.dependency_overrides[get_session] = mock_get_session
        client = TestClient(app=app)

        response = client.delete(
            base_url,
            headers={
                'Authorization': f'Bearer {authenticated_header.access_token}'
            },
        )

        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert response.json() == {'detail': 'Failed to delete user'}
        mock_session.rollback.assert_called_once()
        user_db = session.execute(select(User)).one_or_none()
        assert user_db
    finally:
        app.dependency_overrides.clear()
