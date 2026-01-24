from datetime import timedelta
from http import HTTPStatus
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from madr.config import Settings
from madr.core.redis import redis_manager
from madr.core.security import authenticate_user, generate_token, get_hash
from madr.dependencies import ActiveUser, RequestFormData
from madr.schemas.security import Token
from madr.types import DBSession

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/token', status_code=HTTPStatus.OK, response_model=Token)
async def login(session: DBSession, form_data: RequestFormData) -> Token:
    identity = form_data.username
    password = form_data.password

    result = await authenticate_user(session, identity, password)

    if not (result.authenticated and result.user):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    user = result.user
    user_id = user.id
    username = user.username
    email = user.email

    if result.needs_rehash:
        user.password = get_hash(password)
        await session.commit()

    token_delta_expire_time = timedelta(
        minutes=Settings().ACCESS_TOKEN_EXPIRE_MINUTES  # type: ignore
    )

    version = await redis_manager.get_user_token_version(user_id)
    jti = uuid4()
    data = {
        'sub': user_id,
        'username': username,
        'email': email,
        'jti': str(jti),
        'ver': int(version),
    }
    access_token = generate_token(data, token_delta_expire_time)

    return Token(access_token=access_token, token_type='bearer')


@router.post('/logout', status_code=HTTPStatus.OK)
async def logout(auth_context: ActiveUser):
    """Sair de um único dispositivo"""
    jti = auth_context.jti
    exp = auth_context.exp

    await redis_manager.deny_token(jti, exp)
    return {'message': 'Logged out successfully'}


@router.post('/logout-all', status_code=HTTPStatus.OK)
async def logout_all_devices(auth_context: ActiveUser):
    """Sair de todos os dispositivos"""
    active_user = auth_context.current_user
    await redis_manager.increment_user_token_version(active_user.id)
    return {'message': 'All sessions invalidated'}
