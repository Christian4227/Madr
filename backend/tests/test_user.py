from http import HTTPStatus

import ipdb  # noqa: F401
from fastapi.testclient import TestClient

from madr.models.user import User
from madr.schemas.security import Token
from madr.schemas.user import UserCreate


def test_users_deve_retornar_usuario_criado_com_id(client: TestClient):
    payload = {
        'username': 'pedrinho',
        'email': 'pedrinho@gmail.com.br',
        'password': 'batatinhas',
    }
    response = client.post(
        '/users/',
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
        '/users/',
        json=payload,
    )

    assert response.status_code == HTTPStatus.CONFLICT

    assert response.json() == {'detail': 'User has been exists'}


def test_update_user_deve_retornar_success_delecao(
    client: TestClient, authenticated_header: Token
):
    response = client.delete(
        '/users/',
        headers={
            'Authorization': f'Bearer {authenticated_header.access_token}'
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Account Removed'}


# def test_update_user_deve_retornar_success_delecao(
#     client: TestClient, authenticated_token: Token
# ):

#     response = client.delete(
#         '/users/',
#         headers={
#             'Authorization': f'Bearer : {authenticated_token.access_token}'
#         },
#     )
#     data = response.json()
#     assert data == {'message': 'Account Removed'}


def test_update_user_deve_retornar_user_modificado(
    client: TestClient, user: User, authenticated_header: Token
):
    username = user.username
    modified_username = f'modified_{username}'

    payload = {
        'username': modified_username,
    }

    response = client.put(
        '/users/',
        json=payload,
        headers={
            'Authorization': f'Bearer {authenticated_header.access_token}'
        },
    )

    data = response.json()

    assert data['username'] == modified_username
