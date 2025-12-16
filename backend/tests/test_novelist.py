from datetime import timedelta
from http import HTTPStatus
from unittest.mock import Mock

import ipdb  # noqa: F401
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from madr.core.database import get_session
from madr.models.book import Book
from madr.models.novelist import Novelist
from madr.models.user import User
from madr.schemas.novelists import NovelistSchema
from madr.schemas.security import Token
from tests.utils import frozen_context

url_base = '/novelists/'


def test_create_novelist_deve_retornar_novelist_com_id(
    client: TestClient,
    authenticated_token: Token,
):
    payload = {'name': 'Zaraulstra'}
    response = client.post(
        url_base,
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {**payload, 'id': 1}


def test_create_novelist_deve_falhar_retornar_conflito(
    client: TestClient, authenticated_token: Token, novelist: Novelist
):
    novelist_schema = NovelistSchema.model_validate(
        novelist, from_attributes=True
    )
    payload = novelist_schema.model_dump()
    response = client.post(
        url_base,
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Novelist already exists'}


def test_create_novelist_deve_falhar_com_nao_autorizacao(
    client: TestClient,
):
    payload = {'name': 'Zaraulstra'}
    response = client.post(
        url_base,
        json=payload,
        headers={},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Not authenticated'}


def test_delete_novelist_deve_retornar_success_delecao(
    client: TestClient,
    authenticated_token: Token,
    novelist_with_books: Novelist,
):
    response = client.delete(
        f'/novelists/{novelist_with_books.id}',
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )
    assert response.json() == {'message': 'Novelist Removed'}
    assert response.status_code == HTTPStatus.OK


def test_delete_novelist_e_livros_deve_retornar_success(
    client: TestClient,
    authenticated_token: Token,
    session: Session,
    novelist_with_books: Novelist,
):
    novelist_id = novelist_with_books.id
    response = client.delete(
        f'/novelists/{novelist_id}',
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    books = session.scalars(
        select(Book).where(Book.id_novelist == novelist_id)
    ).all()

    assert len(books) == 0
    assert response.json() == {'message': 'Novelist Removed'}
    assert response.status_code == HTTPStatus.OK


def test_delete_user_deve_retornar_not_found(
    client: TestClient,
    authenticated_token: Token,
    novelist_with_books: Novelist,
):
    response = client.delete(
        f'/novelists/{novelist_with_books.id + 15674}',
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )
    assert response.json() == {'detail': 'Novelist not found'}

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_user_deve_retornar_unauthorized(
    client: TestClient,
    novelist_with_books: Novelist,
):
    response = client.delete(f'/novelists/{novelist_with_books.id}')
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Not authenticated'}


def test_update_novelist_deve_retornar_novelist_modificado(
    client: TestClient,
    novelist: Novelist,
    authenticated_token: Token,
):
    novelist_name = novelist.name
    modified_novelist_name = f'modified_{novelist_name}'

    payload = {
        'name': modified_novelist_name,
    }

    response = client.put(
        f'/novelists/{novelist.id}',
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    data = response.json()

    assert data['name'] == modified_novelist_name


def test_update_novelist_deve_falhar_com_not_found(
    client: TestClient, novelist: Novelist, authenticated_token: Token
):
    novelist_name = novelist.name
    modified_novelist_name = f'modified_{novelist_name}'

    payload = {
        'name': modified_novelist_name,
    }

    response = client.put(
        f'/novelists/{novelist.id + 89749}',
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.NOT_FOUND

    assert response.json() == {'detail': 'Novelist not found'}


def test_update_novelist_deve_falhar_com_rollback(
    session: Session,
    authenticated_token: Token,
    user: User,
    novelist: Novelist,
):
    from madr.app import app  # noqa: PLC0415

    original_name = novelist.name
    mock_session = Mock()
    mock_session.scalar.side_effect = [user, novelist]
    mock_session.commit.side_effect = SQLAlchemyError('DB Error')
    mock_session.rollback = Mock()

    def mock_get_session():
        yield mock_session

    try:
        app.dependency_overrides[get_session] = mock_get_session
        client = TestClient(app=app)

        response = client.put(
            f'/novelists/{novelist.id}',
            json={'name': 'Will Fail'},
            headers={
                'Authorization': f'Bearer {authenticated_token.access_token}'
            },
        )

        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        mock_session.rollback.assert_called_once()
        session.refresh(novelist)
        assert novelist.name == original_name
    finally:
        app.dependency_overrides.clear()


# with frozen_context(timedelta(minutes=31)):
#         response = client.post(
#             base_url,
#             headers={
#                 'Authorization': f'Bearer {authenticated_token.access_token}'
#             },
#             json=book_payload,
#         )
#         data = response.json()
#         # ipdb.set_trace()
#         assert data == {'detail': 'Expired token'}


def test_create_novelist_deve_falhar_com_token_expirado(
    session: Session,
    client: TestClient,
    authenticated_token: Token,
):
    payload = {'name': 'Zaraulstra da Bahia'}

    with frozen_context(timedelta(minutes=31)):
        response = client.post(
            url_base,
            json=payload,
            headers={
                'Authorization': f'Bearer {authenticated_token.access_token}'
            },
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        db_novelist = session.scalar(
            select(Novelist).where(Novelist.name == payload['name'])
        )
        assert db_novelist is None
        assert response.json() == {'detail': 'Expired token'}


def test_update_novelist_deve_falhar_com_token_expirado(
    session: Session,
    client: TestClient,
    novelist: Novelist,
    authenticated_token: Token,
):
    novelist_name = novelist.name
    modified_novelist_name = f'modified_{novelist_name}'

    payload = {
        'name': modified_novelist_name,
    }
    with frozen_context(timedelta(minutes=31)):
        response = client.put(
            f'/novelists/{novelist.id}',
            json=payload,
            headers={
                'Authorization': f'Bearer {authenticated_token.access_token}'
            },
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        db_novelist = session.scalar(
            select(Novelist).where(Novelist.name == payload['name'])
        )
        assert db_novelist is None
        assert response.json() == {'detail': 'Expired token'}
