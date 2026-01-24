from datetime import timedelta
from http import HTTPStatus
from uuid import uuid4

import pytest
from httpx import AsyncClient

from madr.core.redis import redis_manager
from madr.core.security import generate_token
from madr.models.user import User
from madr.schemas.security import Token


@pytest.mark.asyncio
async def test_login_creates_token_with_version(
    client: AsyncClient, user: User
):
    """Test login endpoint creates token with version from Redis"""
    response = await client.post(
        '/auth/token',
        data={'username': user.username, 'password': '123456789'},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert 'access_token' in data
    assert data['token_type'] == 'bearer'


@pytest.mark.asyncio
async def test_logout_deny_token(
    client: AsyncClient, authenticated_token: Token
):
    """Testa logout deve adicionar token na lista de negação"""
    auth_header = {
        'Authorization': f'Bearer {authenticated_token.access_token}'
    }

    response = await client.get('/users/me', headers=auth_header)
    assert response.status_code == HTTPStatus.OK

    response = await client.post('/auth/logout', headers=auth_header)
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Logged out successfully'}

    response = await client.get('/users/me', headers=auth_header)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert 'Session invalidated' in response.json()['detail']


@pytest.mark.asyncio
async def test_logout_all_invalidates_all_tokens(
    client: AsyncClient, user: User, authenticated_token: Token
):
    """Test logout-all increments version and invalidates all tokens"""
    token1 = authenticated_token.access_token

    # Create second token
    jti2 = uuid4()
    version = await redis_manager.get_user_token_version(user.id)
    data2 = {
        'sub': user.id,
        'username': user.username,
        'email': user.email,
        'jti': str(jti2),
        'ver': version,
    }
    token2 = generate_token(data2, timedelta(minutes=30))

    # Both tokens work
    response = await client.get(
        '/users/me', headers={'Authorization': f'Bearer {token1}'}
    )
    assert response.status_code == HTTPStatus.OK

    response = await client.get(
        '/users/me', headers={'Authorization': f'Bearer {token2}'}
    )
    assert response.status_code == HTTPStatus.OK

    # Logout all
    response = await client.post(
        '/auth/logout-all', headers={'Authorization': f'Bearer {token1}'}
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'All sessions invalidated'}

    # Both tokens invalid now
    response = await client.get(
        '/users/me', headers={'Authorization': f'Bearer {token1}'}
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = await client.get(
        '/users/me', headers={'Authorization': f'Bearer {token2}'}
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.asyncio
async def test_new_login_after_logout_all_works(
    client: AsyncClient, user: User, authenticated_token: Token
):
    """Test new login after logout-all creates valid token"""
    old_token = authenticated_token.access_token

    await client.post(
        '/auth/logout-all', headers={'Authorization': f'Bearer {old_token}'}
    )

    response = await client.get(
        '/users/me', headers={'Authorization': f'Bearer {old_token}'}
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = await client.post(
        '/auth/token',
        data={'username': user.username, 'password': '123456789'},
    )
    assert response.status_code == HTTPStatus.OK
    new_token = response.json()['access_token']

    response = await client.get(
        '/users/me', headers={'Authorization': f'Bearer {new_token}'}
    )
    assert response.status_code == HTTPStatus.OK


@pytest.mark.asyncio
async def test_redis_manager_denylist_token():
    """Test Redis manager denylist operations"""
    jti = str(uuid4())
    exp = 1800000000

    await redis_manager.deny_token(jti, exp)

    is_denylisted = await redis_manager.is_token_denyed_list(jti)
    assert is_denylisted is True

    is_denylisted = await redis_manager.is_token_denyed_list('nonexistent')
    assert is_denylisted is False


@pytest.mark.asyncio
async def test_redis_manager_token_version():
    """Tests operações base do Redis manager"""
    user_id = 999

    version = await redis_manager.get_user_token_version(user_id)
    assert version == 0  # noqa: PLR2004

    new_version = await redis_manager.increment_user_token_version(user_id)
    assert new_version == 1  # noqa: PLR2004

    version = await redis_manager.get_user_token_version(user_id)
    assert version == 1  # noqa: PLR2004

    new_version = await redis_manager.increment_user_token_version(user_id)
    assert new_version == 2  # noqa: PLR2004


@pytest.mark.asyncio
async def test_multiple_logout_same_token(
    client: AsyncClient, authenticated_token: Token
):
    """Testa logou como o mesmo tokeb duas vezes"""
    token = authenticated_token.access_token

    response = await client.post(
        '/auth/logout', headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == HTTPStatus.OK

    response = await client.post(
        '/auth/logout', headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
