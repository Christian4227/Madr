from datetime import timedelta
from http import HTTPStatus
from unittest.mock import Mock, patch

import ipdb  # noqa: F401
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from madr.app import app
from madr.core.database import get_session
from madr.models.book import Book
from madr.models.novelist import Novelist
from madr.models.user import User
from madr.schemas.books import BookPublic
from madr.schemas.security import Token
from tests.utils import frozen_context

base_url = '/books/'


# ============================================================================
# CREATE TESTS
# ============================================================================


def test_create_book_deve_ter_exito_e_retornar_book_com_id(
    client: TestClient,
    authenticated_token: Token,
    book_payload: dict,
):
    response = client.post(
        base_url,
        json=book_payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )
    assert response.status_code == HTTPStatus.CREATED


def test_create_book_deve_falhar_com_conflict(
    session: Session,
    client: TestClient,
    authenticated_token: Token,
    book: Book,
):
    response = client.post(
        base_url,
        json={
            'idNovelist': book.id_novelist,
            'name': book.name,
            'year': '2017',
            'title': 'Modified Title',
        },
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Book already exists'

    db_books = session.scalars(
        select(Book).where(Book.name == book.name)
    ).all()
    assert len(db_books) == 1


def test_create_book_deve_falhar_por_nao_existir_romancista(
    session: Session,
    authenticated_token: Token,
    client: TestClient,
    book_payload: dict,
):
    book_payload['idNovelist'] = 99999
    response = client.post(
        base_url,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
        json=book_payload,
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Novelist not found'}

    db_book = session.scalar(
        select(Book).where(Book.name == book_payload['name'])
    )
    assert db_book is None


def test_create_book_deve_falhar_sem_authorization(
    client: TestClient,
    book_payload: dict,
):
    response = client.post(base_url, json=book_payload)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()['detail'] == 'Not authenticated'


def test_create_book_deve_falhar_sem_token_valido(
    client: TestClient,
    book_payload: dict,
):
    response = client.post(
        base_url,
        headers={'Authorization': 'Bearer eyasdasdasd'},
        json=book_payload,
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()['detail'] == 'Could not validate credentials'


def test_create_book_deve_falhar_por_token_expirado(
    session: Session,
    authenticated_token: Token,
    client: TestClient,
    book_payload: dict,
):
    with frozen_context(timedelta(minutes=31)):
        response = client.post(
            base_url,
            headers={
                'Authorization': f'Bearer {authenticated_token.access_token}'
            },
            json=book_payload,
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json() == {'detail': 'Expired token'}

        db_book = session.scalar(
            select(Book).where(Book.name == book_payload['name'])
        )
        assert db_book is None


def test_create_book_deve_falhar_user_removido(
    authenticated_token: Token,
    book_payload: dict,
    client: TestClient,
    session: Session,
):
    session.execute(delete(User))
    session.commit()

    response = client.post(
        base_url,
        json=book_payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


@pytest.mark.parametrize(
    'field_missing',
    ['name', 'year', 'title', 'idNovelist'],
)
def test_create_book_deve_falhar_sem_campos_obrigatorios(
    field_missing: str,
    client: TestClient,
    authenticated_token: Token,
    book_payload: dict,
):
    del book_payload[field_missing]
    response = client.post(
        base_url,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
        json=book_payload,
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    errors = response.json()['detail']
    assert any(
        err['type'] == 'missing' and err['loc'][1] == field_missing
        for err in errors
    )


@pytest.mark.parametrize(
    'field',
    ['name', 'year', 'title', 'idNovelist'],
)
def test_create_book_deve_falhar_com_null_em_campos_obrigatorios(
    field: str,
    client: TestClient,
    authenticated_token: Token,
    book_payload: dict,
):
    book_payload[field] = None
    response = client.post(
        base_url,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
        json=book_payload,
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    errors = response.json()['detail']
    assert any(err['loc'][1] == field for err in errors)


def test_create_book_deve_falhar_com_erro_de_banco_e_rollback(
    session: Session,
    authenticated_token: Token,
    book_payload: dict,
    user: User,
):
    mock_session = Mock(spec=Session)
    mock_session.scalar.return_value = user
    mock_session.commit.side_effect = SQLAlchemyError('Database error')

    def mock_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = mock_get_session
    client = TestClient(app=app)

    response = client.post(
        base_url,
        json=book_payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {'detail': 'Database error'}
    mock_session.rollback.assert_called_once()

    db_book = session.scalar(
        select(Book).where(Book.name == book_payload['name'])
    )
    assert db_book is None


def test_create_book_deve_falhar_integrity_error_generico(
    authenticated_token: Token,
    book_payload: dict,
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
        base_url,
        json=book_payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Integrity violation'}
    mock_session.rollback.assert_called_once()


def test_create_book_falha_exception_generica(
    authenticated_token: Token, book_payload: dict, user: User
):
    mock_session = Mock(spec=Session)
    mock_session.scalar.return_value = user
    mock_session.commit.side_effect = Exception('Unexpected error')

    def mock_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = mock_get_session
    client = TestClient(app)

    response = client.post(
        base_url,
        json=book_payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {'detail': 'Internal error'}


# ============================================================================
# UPDATE TESTS
# ============================================================================


def test_update_book_deve_ter_exito_e_retornar_book_modificado(
    client: TestClient,
    authenticated_token: Token,
    book: Book,
):
    payload = {'title': 'Modified Title'}
    response = client.put(
        f'{base_url}{book.id}',
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()['title'] == 'Modified Title'


def test_update_book_deve_falhar_book_not_found(
    client: TestClient,
    authenticated_token: Token,
):
    payload = {'title': 'Modified Title'}
    response = client.put(
        f'{base_url}99999',
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Book not found'}


def test_update_book_deve_falhar_por_nao_existir_romancista(
    novelist: Novelist,
    session: Session,
    authenticated_token: Token,
    client: TestClient,
    book: Book,
):
    payload = {'idNovelist': novelist.id + 10}
    response = client.put(
        f'{base_url}{book.id}',
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
        json=payload,
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Novelist not found'}


def test_update_book_deve_falhar_unique_violation(
    book: Book,
    client: TestClient,
    authenticated_token: Token,
    session: Session,
):
    book_name_existent = book.name

    other_book = Book(
        name='other_book',
        year='2020',
        title='Other',
        id_novelist=book.id_novelist,
    )
    session.add(other_book)
    session.commit()

    response = client.put(
        f'{base_url}{other_book.id}',
        json={'name': book_name_existent},
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Book already exists'}


def test_update_book_deve_falhar_com_erro_de_banco_e_rollback(
    authenticated_token: Token,
    user: User,
    book: Book,
):
    mock_session = Mock(spec=Session)
    mock_session.scalar.side_effect = [user, book]
    mock_session.commit.side_effect = SQLAlchemyError('DB Error')

    def mock_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = mock_get_session
    client = TestClient(app=app)

    response = client.put(
        f'{base_url}{book.id}',
        json={'title': 'New Title'},
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {'detail': 'Database error'}
    mock_session.rollback.assert_called_once()


def test_update_book_deve_falhar_integrity_error_generico(
    authenticated_token: Token,
    user: User,
    book: Book,
):
    mock_session = Mock(spec=Session)
    mock_session.scalar.side_effect = [user, book]
    mock_session.commit.side_effect = IntegrityError(
        'statement', 'params', Exception('check constraint failed')
    )

    def mock_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = mock_get_session
    client = TestClient(app=app)

    response = client.put(
        f'{base_url}{book.id}',
        json={'title': 'New Title'},
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {'detail': 'Database error'}
    mock_session.rollback.assert_called_once()


# ============================================================================
# DELETE TESTS
# ============================================================================
def test_delete_book_deve_ter_sucesso_e_retornar_mensagem(
    client: TestClient,
    authenticated_token: Token,
    session: Session,
    book: Book,
):
    response = client.delete(
        f'{base_url}{book.id}',
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Book Removed'}


def test_delete_book_by_id_deve_falhar_e_retornar_exception(
    client: TestClient,
    authenticated_token: Token,
    session: Session,
    book: Book,
):
    response = client.delete(
        f'{base_url}{book.id + 999}',
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )
    assert response.status_code == HTTPStatus.NOT_FOUND

    assert response.json() == {'detail': 'Book not found'}


def test_delete_book_by_id_deve_falhar_com_rollback(
    client: TestClient,
    authenticated_token: Token,
    session: Session,
    book: Book,
):
    original_book_id = book.id

    with patch.object(
        session, 'commit', side_effect=SQLAlchemyError('DB Error')
    ):
        response = client.delete(
            f'{base_url}{original_book_id}',
            headers={
                'Authorization': f'Bearer {authenticated_token.access_token}'
            },
        )

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    assert response.json() == {'detail': 'Database error'}

    session.expire_all()
    db_book = session.scalar(select(Book).where(Book.id == original_book_id))
    assert db_book is not None
    assert db_book.id == original_book_id


# ============================================================================
# READ TESTS
# ============================================================================
def test_read_books_by_partial_name_title_deve_ter_sucesso_e_retornar_books(
    client: TestClient,
    session: Session,
    book: Book,
):
    ...


def test_read_book_by_id_deve_ter_sucesso_e_retornar_book(
    client: TestClient,
    session: Session,
    book: Book,
):
    response = client.get(f'{base_url}{book.id}')
    assert response.status_code == HTTPStatus.OK
    _book_schema = BookPublic.model_validate(book)
    assert response.json() == _book_schema.model_dump()


def test_read_book_by_id_deve_falhar_e_retornar_exception(
    client: TestClient,
    session: Session,
    book: Book,
):
    response = client.get(f'{base_url}{book.id + 999}')
    assert response.status_code == HTTPStatus.NOT_FOUND

    assert response.json() == {'detail': 'Book not found'}
