from http import HTTPStatus

import ipdb  # noqa: F401
from fastapi.testclient import TestClient

from madr.core.security import Token
from madr.models.user import User


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


def test_users_deve_retornar_token_de_usuario_autenticado(
    client: TestClient, user: User
):
    payload = {
        'username': user.email,
        'password': '123456789',
    }
    response = client.post('/users/token', data=payload)
    data = response.json()

    assert 'access_token' in data
    assert 'token_type' in data
    assert data['access_token'].startswith('ey')
    assert data['token_type'] == 'bearer'
