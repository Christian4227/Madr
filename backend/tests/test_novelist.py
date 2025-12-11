from http import HTTPStatus

import ipdb  # noqa: F401
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from madr.models.book import Book
from madr.models.novelist import Novelist
from madr.schemas.novelists import NovelistSchema
from madr.schemas.security import Token


def test_novelist_deve_criar_e_retornar_novelist_com_id(
    client: TestClient,
    authenticated_header: Token,
):
    payload = {'name': 'Zaraulstra'}
    response = client.post(
        '/novelists/',
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_header.access_token}'
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {**payload, 'id': 1}


def test_novelist_deve_falhar_ao_criar_e_retornar_conflito(
    client: TestClient, authenticated_header: Token, novelist: Novelist
):
    novelist_schema = NovelistSchema.model_validate(
        novelist, from_attributes=True
    )
    payload = novelist_schema.model_dump()
    response = client.post(
        '/novelists/',
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_header.access_token}'
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Novelist has been exists'}


def test_novelist_deve_falhar_na_criacao_por_nao_autorizado(
    client: TestClient,
):
    payload = {'name': 'Zaraulstra'}
    response = client.post(
        '/novelists/',
        json=payload,
        headers={},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Not authenticated'}


def test_remocao_novelist_deve_retornar_success_delecao(
    client: TestClient,
    authenticated_header: Token,
    session: Session,
    novelist_with_books: Novelist,
):
    response = client.delete(
        f'/novelists/{novelist_with_books.id}',
        headers={
            'Authorization': f'Bearer {authenticated_header.access_token}'
        },
    )
    assert response.json() == {'message': 'Novelist Removed'}
    assert response.status_code == HTTPStatus.OK


def test_remocao_novelist_e_livros_deve_retornar_success_delecao(
    client: TestClient,
    authenticated_header: Token,
    session: Session,
    novelist_with_books: Novelist,
):
    novelist_id = novelist_with_books.id
    response = client.delete(
        f'/novelists/{novelist_id}',
        headers={
            'Authorization': f'Bearer {authenticated_header.access_token}'
        },
    )

    books = session.scalars(
        select(Book).where(Book.id_novelist == novelist_id)
    ).all()
    assert len(books) == 0

    assert response.json() == {'message': 'Novelist Removed'}
    assert response.status_code == HTTPStatus.OK


def test_remocao_user_deve_retornar_not_found_na_delecao(
    client: TestClient,
    authenticated_header: Token,
    novelist_with_books: Novelist,
):
    response = client.delete(
        f'/novelists/{novelist_with_books.id + 15674}',
        headers={
            'Authorization': f'Bearer {authenticated_header.access_token}'
        },
    )
    assert response.json() == {'detail': 'Novelist not found'}

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_remocao_user_deve_retornar_unauthorized_na_delecao(
    client: TestClient,
    authenticated_header: Token,
    novelist_with_books: Novelist,
):
    response = client.delete(f'/novelists/{novelist_with_books.id}')
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Not authenticated'}


def test_update_novelist_deve_retornar_novelist_modificado(
    client: TestClient, novelist: Novelist, authenticated_header: Token
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
            'Authorization': f'Bearer {authenticated_header.access_token}'
        },
    )

    data = response.json()

    assert data['name'] == modified_novelist_name


# # def test_update_user_deve_retornar_success_delecao(
# #     client: TestClient, authenticated_token: Token
# # ):

# #     response = client.delete(
# #         '/users/',
# #         headers={
# #             'Authorization': f'Bearer : {authenticated_token.access_token}'
# #         },
# #     )
# #     data = response.json()
# #     assert data == {'message': 'Account Removed'}


# def test_novelist_deve_retornar_token_de_usuario_autenticado(
#     client: TestClient, user: User
# ):
#     payload = {
#         'username': user.email,
#         'password': '123456789',
#     }
#     response = client.post('/auth/token', data=payload)
#     data = response.json()
#     assert 'access_token' in data
#     assert 'token_type' in data
#     assert data['access_token'].startswith('ey')
#     assert data['token_type'] == 'bearer'
