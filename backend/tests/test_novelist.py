from datetime import timedelta
from http import HTTPStatus
from typing import Callable, Optional
from unittest.mock import Mock
from urllib.parse import urlencode

import ipdb  # noqa: F401
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from madr.app import app
from madr.core.database import get_session
from madr.models.book import Book
from madr.models.novelist import Novelist
from madr.models.user import User
from madr.schemas.novelists import NovelistSchema
from madr.schemas.security import Token
from tests.utils import frozen_context

url_base = '/novelists/'


# ============================================================================
# CREATE TESTS
# ============================================================================


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
    response = client.post(url_base, json=payload, headers={})
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Not authenticated'}


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
        assert response.json() == {'detail': 'Expired token'}

        db_novelist = session.scalar(
            select(Novelist).where(Novelist.name == payload['name'])
        )
        assert db_novelist is None


def test_create_novelist_deve_falhar_com_erro_de_banco(
    authenticated_token: Token,
    user: User,
):
    mock_session = Mock(spec=Session)
    mock_session.scalar.return_value = user
    mock_session.commit.side_effect = IntegrityError(
        'statement', 'params', Exception('check constraint failed')
    )

    def mock_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = mock_get_session
    client = TestClient(app=app)

    response = client.post(
        url_base,
        json={'name': 'Test Novelist'},
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {'detail': 'Database error'}
    mock_session.rollback.assert_called_once()


# ============================================================================
# UPDATE TESTS
# ============================================================================


def test_update_novelist_deve_retornar_novelist_modificado(
    client: TestClient,
    novelist: Novelist,
    authenticated_token: Token,
):
    modified_name = f'modified_{novelist.name}'
    payload = {'name': modified_name}

    response = client.put(
        f'{url_base}{novelist.id}',
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()['name'] == modified_name


def test_update_novelist_deve_falhar_com_not_found(
    client: TestClient, novelist: Novelist, authenticated_token: Token
):
    payload = {'name': f'modified_{novelist.name}'}

    response = client.put(
        f'{url_base}{novelist.id + 89749}',
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Novelist not found'}


def test_update_novelist_deve_falhar_unique_violation(
    client: TestClient,
    session: Session,
    authenticated_token: Token,
):
    novelist1 = Novelist(name='Novelist One')
    novelist2 = Novelist(name='Novelist Two')
    session.add_all([novelist1, novelist2])
    session.commit()

    response = client.put(
        f'{url_base}{novelist2.id}',
        json={'name': novelist1.name},
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Novelist already exists'}


def test_update_novelist_deve_falhar_com_rollback(
    session: Session,
    authenticated_token: Token,
    user: User,
    novelist: Novelist,
):
    original_name = novelist.name
    mock_session = Mock(spec=Session)
    mock_session.scalar.side_effect = [user, novelist]
    mock_session.commit.side_effect = SQLAlchemyError('DB Error')

    def mock_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = mock_get_session
    client = TestClient(app=app)

    response = client.put(
        f'{url_base}{novelist.id}',
        json={'name': 'Will Fail'},
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    # ipdb.set_trace()
    assert response.json() == {'detail': 'Database error'}
    mock_session.rollback.assert_called_once()

    session.refresh(novelist)
    assert novelist.name == original_name


def test_update_novelist_deve_falhar_com_token_expirado(
    session: Session,
    client: TestClient,
    novelist: Novelist,
    authenticated_token: Token,
):
    modified_name = f'modified_{novelist.name}'
    payload = {'name': modified_name}

    with frozen_context(timedelta(minutes=31)):
        response = client.put(
            f'{url_base}{novelist.id}',
            json=payload,
            headers={
                'Authorization': f'Bearer {authenticated_token.access_token}'
            },
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json() == {'detail': 'Expired token'}

        db_novelist = session.scalar(
            select(Novelist).where(Novelist.name == payload['name'])
        )
        assert db_novelist is None


# ============================================================================
# READ TESTS
# ============================================================================


def test_read_books_of_novelist_deve_retornar_lista_de_livros_de_um_romancista(
    client: TestClient,
    novelist_with_books: Callable[[int], Novelist],
):
    novelist = novelist_with_books(350)
    response = client.get(f'{url_base}{novelist.id}/books')
    response_data = response.json()

    assert response.status_code == HTTPStatus.OK

    assert len(response_data['data'])


def test_read_books_of_novelist_deve_retornar_livros_de_um_romancista_com_limit_e_offset(  # noqa: E501
    client: TestClient,
    novelist_with_books: Callable[[int], Novelist],
):
    total_books = 43
    limit = 8
    page = 6
    params = {'limit': limit, 'page': page}
    query_string = urlencode(params)

    partial_page_qty = total_books - ((page - 1) * limit)

    novelist = novelist_with_books(total_books)

    url = f'{url_base}{novelist.id}/books?{query_string}'
    response = client.get(url)
    response_data = response.json()

    assert response.status_code == HTTPStatus.OK

    assert len(response_data['data']) == partial_page_qty


def test_read_books_of_novelist_deve_retornar_0_livros_por_pagina_inexistente(
    client: TestClient,
    novelist_with_books: Callable[[int], Novelist],
):
    total_books = 25
    limit = 10
    page = 4
    params = {'limit': limit, 'page': page}
    query_string = urlencode(params)
    novelist = novelist_with_books(total_books)

    url = f'{url_base}{novelist.id}/books?{query_string}'
    response = client.get(url)
    response_data = response.json()

    assert response.status_code == HTTPStatus.OK

    assert response_data == {
        'data': [],
        'total': 0,
        'page': page,
        'hasPrev': True,
        'hasNext': False,
    }


def test_read_books_of_novelist_deve_retornar_0_livros_por_pagina_muito_acima_da_ultima_existente(  # noqa: E501
    client: TestClient,
    novelist_with_books: Callable[[int], Novelist],
):
    total_books = 50
    limit = 10
    page = 9
    params = {'limit': limit, 'page': page}
    query_string = urlencode(params)

    novelist = novelist_with_books(total_books)

    url = f'{url_base}{novelist.id}/books?{query_string}'
    response = client.get(url)
    response_data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert response_data == {
        'data': [],
        'total': 0,
        'page': page,
        'hasPrev': True,
        'hasNext': False,
    }


def test_read_books_of_novelist_deve_retornar_zero_livros_de_um_romancista(
    client: TestClient,
    novelist_with_books: Callable[[int], Novelist],
):
    total_books = 0
    params = {'limit': 10, 'page': 6}
    query_string = urlencode(params)
    novelist = novelist_with_books(total_books)

    url = f'{url_base}{novelist.id}/books?{query_string}'
    response = client.get(url)

    response_data = response.json()
    assert response.status_code == HTTPStatus.OK

    assert len(response_data['data']) == 0


@pytest.mark.parametrize('order_dir', ['asc', 'desc'])
@pytest.mark.parametrize('order_by', ['title', 'name', 'year'])
def test_read_books_of_novelist_deve_retornar_livros_ordenados(
    client: TestClient,
    novelist_with_books: Callable[
        [int, Optional[str], Optional[str]], Novelist
    ],
    order_by: str,
    order_dir: str,
):
    total_books = 50
    params = {
        'limit': 8,
        'page': 5,
        'orderBy': order_by,
        'orderDir': order_dir,
    }
    query_string = urlencode(params)
    novelist = novelist_with_books(total_books)

    url = f'{url_base}{novelist.id}/books?{query_string}'
    response = client.get(url)
    # ipdb.set_trace()
    response_data = response.json()
    assert response.status_code == HTTPStatus.OK

    sorted_data = sorted(
        response_data['data'],
        key=lambda book: book[order_by],
        reverse=(order_dir == 'desc'),
    )
    assert response_data['data'] == sorted_data


# ============================================================================
# DELETE TESTS
# ============================================================================


def test_delete_novelist_deve_retornar_success_delecao(
    client: TestClient,
    authenticated_token: Token,
    novelist_with_books: Callable[[int], Novelist],
):
    novelist = novelist_with_books(25)
    response = client.delete(
        f'{url_base}{novelist.id}',
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Novelist Removed'}


def test_delete_novelist_e_livros_deve_retornar_success(
    client: TestClient,
    authenticated_token: Token,
    session: Session,
    novelist_with_books: Callable[[int], Novelist],
):
    novelist = novelist_with_books(15)
    novelist_id = novelist.id

    response = client.delete(
        f'{url_base}{novelist_id}',
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Novelist Removed'}

    db_books = session.scalars(
        select(Book).where(Book.id_novelist == novelist_id)
    ).all()
    assert len(db_books) == 0


def test_delete_novelist_deve_retornar_not_found(
    session: Session,
    client: TestClient,
    authenticated_token: Token,
    novelist_with_books: Callable[[int], Novelist],
):
    novelist = novelist_with_books(15)
    stmt = select(func.max(Novelist.id))
    max_id = session.scalar(stmt)
    last_id_novelist = 0 if max_id is None else max_id

    response = client.delete(
        f'{url_base}{last_id_novelist + 1}',
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )
    db_novelist = session.scalar(
        select(Novelist).where(Novelist.id == novelist.id)
    )
    assert db_novelist
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Novelist not found'}


def test_delete_novelist_deve_retornar_unauthorized(
    client: TestClient,
    novelist_with_books: Callable[[int], Novelist],
):
    novelist = novelist_with_books(15)
    response = client.delete(f'{url_base}{novelist.id}')
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Not authenticated'}


def test_delete_novelist_deve_falhar_com_rollback(
    authenticated_token: Token,
    user: User,
    novelist: Novelist,
    session: Session,
):
    mock_session = Mock(spec=Session)
    mock_session.scalar.side_effect = [user, novelist]
    mock_session.delete = Mock()
    mock_session.commit.side_effect = SQLAlchemyError('DB Error')

    def mock_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = mock_get_session
    client = TestClient(app=app)

    response = client.delete(
        f'{url_base}{novelist.id}',
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {
        'detail': 'Cannot delete novelist with existing references'
    }
    mock_session.rollback.assert_called_once()

    # Verifica que não foi deletado
    db_novelist = session.scalar(
        select(Novelist).where(Novelist.id == novelist.id)
    )
    assert db_novelist is not None
