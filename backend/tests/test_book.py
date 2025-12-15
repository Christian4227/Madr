from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from unittest.mock import Mock

import ipdb  # noqa: F401
import pytest
from fastapi.testclient import TestClient
from freezegun import freeze_time
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from madr.models.book import Book
from madr.models.user import User
from madr.schemas.security import Token

base_url = '/books/'


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
    data = response.json()
    assert data['idNovelist'] == book_payload['idNovelist']


def test_create_book_deve_falhar_com_conflict(
    session: Session,
    client: TestClient,
    authenticated_token: Token,
    book: Book,
):

    response = client.post(
        base_url,
        json={
            'id_novelist': book.id_novelist,
            'name': book.name,
            'year': '2017',
            'title': 'The First Fifteen Lives of Harry August',
        },
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Book already exists'

    books = session.scalars(select(Book).where(Book.name == book.name)).all()

    assert len(books) == 1


def test_create_book_deve_falhar_com_erro_de_banco_e_rollback(
    session: Session,
    authenticated_token: Token,
    book_payload: dict,
    user: User,
):
    from madr.app import app  # noqa: PLC0415
    from madr.core.database import get_session  # noqa: PLC0415

    mock_session = Mock()
    mock_session.scalar.side_effect = [user, None]
    mock_session.commit.side_effect = SQLAlchemyError('DB Error')
    mock_session.rollback = Mock()

    def mock_get_session():
        yield mock_session

    try:
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

        # Verifica que livro não foi criado no banco real
        book_db = session.scalar(
            select(Book).where(Book.name == book_payload['name'])
        )
        assert book_db is None
    finally:
        app.dependency_overrides.clear()


def test_create_book_deve_falhar_por_token_expirado(
    session: Session,
    authenticated_token: Token,
    client: TestClient,
    book_payload: dict,
):
    initial_datetime = datetime.now(timezone.utc) + timedelta(minutes=6)
    with freeze_time(initial_datetime) as frozen_datetime:  # noqa: F841
        response = client.post(
            base_url,
            headers={
                'Authorization': f'Bearer {authenticated_token.access_token}'
            },
            json=book_payload,
        )
        data = response.json()
        db_book = session.scalar(
            select(Book).where(Book.name == book_payload['name'])
        )

        assert db_book is None
        assert data == {'detail': 'Expired token'}


def test_create_book_deve_falhar_por_nao_existir_romancista(
    session: Session,
    authenticated_token: Token,
    client: TestClient,
    book_payload: dict,
):
    # aponta pra romacista inexistente
    book_payload['idNovelist'] = '99999'
    response = client.post(
        base_url,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
        json=book_payload,
    )

    db_book = session.scalar(
        select(Book).where(Book.name == book_payload['name'])
    )
    data = response.json()

    assert db_book is None
    assert data == {'detail': 'Novelist not found'}
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_create_book_deve_falhar_sem_token_valido(
    client: TestClient,
    book_payload: dict,
):
    response = client.post(
        base_url,
        headers={'Authorization': 'Bearer eyasdasdasd'},
        json=book_payload,
    )
    data = response.json()

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert data['detail'] == 'Could not validate credentials'


def test_create_book_deve_falhar_sem_authorization(
    client: TestClient,
    book_payload: dict,
):
    response = client.post(
        base_url,
        json=book_payload,
    )
    data = response.json()

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert data['detail'] == 'Not authenticated'


@pytest.mark.parametrize(
    'field_missing',
    ['name', 'year', 'title', 'idNovelist'],
)
def test_create_book_deve_falhar_sem_campos_obrigatorios(
    field_missing,
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
    data = response.json()
    for detail in data['detail']:
        if detail['type'] == 'missing':
            assert field_missing == detail['loc'][1]

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_create_book_deve_falhar_user_removido(
    authenticated_token: Token,
    book_payload: dict,
    client: TestClient,
    session: Session,
):
    # remover o user a qual o access_token pertence
    session.execute(delete(User))
    response = client.post(
        base_url,
        json=book_payload,
        headers={
            'Authorization': f'Bearer {authenticated_token.access_token}'
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    data = response.json()
    assert data == {'detail': 'Could not validate credentials'}


def test_create_book_deve_falhar_integrity_error_generico(
    authenticated_token: Token,
    book_payload: dict,
    user: User,
):
    from sqlalchemy.exc import IntegrityError  # noqa: PLC0415

    from madr.app import app  # noqa: PLC0415
    from madr.core.database import get_session  # noqa: PLC0415

    mock_session = Mock()
    mock_session.scalar.side_effect = [user, None]
    # IntegrityError que não é FK nem unique
    mock_session.commit.side_effect = IntegrityError(
        'statement', 'params', Exception('check constraint failed')
    )
    mock_session.rollback = Mock()

    def mock_get_session():
        yield mock_session

    try:
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
    finally:
        app.dependency_overrides.clear()


def test_create_book_deve_falhar_exception_generica(
    authenticated_token: Token,
    book_payload: dict,
    user: User,
):
    from madr.app import app  # noqa: PLC0415
    from madr.core.database import get_session  # noqa: PLC0415

    mock_session = Mock()
    mock_session.scalar.side_effect = [user, None]
    mock_session.commit.side_effect = Exception('Unexpected error')

    def mock_get_session():
        yield mock_session

    try:
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
        assert response.json() == {'detail': 'Internal error'}
    finally:
        app.dependency_overrides.clear()


def test_update_book_deve_ter_exito_e_retornar_book_modificado(
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
    data = response.json()
    assert data['idNovelist'] == book_payload['idNovelist']
