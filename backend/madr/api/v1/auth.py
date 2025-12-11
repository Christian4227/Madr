from datetime import timedelta
from http import HTTPStatus

import ipdb  # noqa: F401
from fastapi import APIRouter, HTTPException

from madr.core.security import (
    authenticate_user,
    generate_token,
    get_hash,
)
from madr.dependecies import db_session, request_form_data
from madr.schemas.security import Token

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/token', status_code=HTTPStatus.OK, response_model=Token)
def login(form_data: request_form_data, session: db_session) -> Token:
    identity = form_data.username
    password = form_data.password
    result = authenticate_user(session, identity, password)

    if not (result.authenticated and result.user):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    user = result.user
    if result.needs_rehash:
        user.password = get_hash(password)
        session.add(user)
        session.commit()

    token_delta_expire_time = timedelta(minutes=5)
    data = {'sub': user.id, 'username': user.username, 'email': user.email}
    access_token = generate_token(data, token_delta_expire_time)

    return Token(access_token=access_token, token_type='bearer')
