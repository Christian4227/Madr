from http import HTTPStatus
from unittest.mock import Mock

import ipdb  # noqa: F401
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from madr.models.book import Book
from madr.models.novelist import Novelist
from madr.models.user import User
from madr.schemas.books import BookCreate
from madr.schemas.security import Token
from tests.factories import BookFactory

base_url = '/books/'


def test_create_book_deve_retornar_book_com_id(
    client: TestClient,
    novelist: Novelist,
    authenticated_header: Token,
):
    book = BookFactory.build(id_novelist=novelist.id)
    book_validated = BookCreate.model_validate(book, from_attributes=True)
    payload = book_validated.model_dump()

    response = client.post(
        base_url,
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_header.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['id_novelist'] == novelist.id


def test_create_book_deve_falhar_com_conflict(
    client: TestClient, authenticated_header: Token, book: Book
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
            'Authorization': f'Bearer {authenticated_header.access_token}'
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT

    assert response.json() == {'detail': 'Book has been exists'}


def test_create_book_deve_falhar_com_rollback(
    session: Session,
    authenticated_header: Token,
    novelist: Novelist,
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
        book = BookFactory.build(id_novelist=novelist.id)
        book_validated = BookCreate.model_validate(book, from_attributes=True)
        payload = book_validated.model_dump()

        app.dependency_overrides[get_session] = mock_get_session
        client = TestClient(app=app)

        response = client.post(
            base_url,
            json=payload,
            headers={
                'Authorization': f'Bearer {authenticated_header.access_token}'
            },
        )

        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert response.json() == {'detail': 'Failed to create book'}
        mock_session.rollback.assert_called_once()

        # Verifica que livro não foi criado no banco real
        book_db = session.scalar(
            select(Book).where(Book.name == payload['name'])
        )
        assert book_db is None
    finally:
        app.dependency_overrides.clear()
