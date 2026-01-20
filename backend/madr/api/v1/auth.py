from datetime import timedelta
from http import HTTPStatus
from uuid import uuid4

import ipdb  # noqa: F401
from fastapi import APIRouter, HTTPException

from madr.config import Settings

# from madr.core.redis import get_user_token_version
from madr.core.security import (
    authenticate_user,
    generate_token,
    get_hash,
)
from madr.dependencies import RequestFormData
from madr.schemas.security import Token

# from madr.types import DBSession, T_redis
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

    # version = await get_user_token_version(redis_client, user_id)

    version = '0'
    # version = await get_user_token_version(redis_client, user_id)
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
