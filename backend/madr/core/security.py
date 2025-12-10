from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from typing import Annotated, Optional

import ipdb  # noqa: F401
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from madr.config import Settings
from madr.core.database import get_session
from madr.models.user import User

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

settings = Settings()  # type: ignore


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[Session, Depends(get_session)],
):  # noqa: F821
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        payload['sub'] = int(payload['sub'])
        int_identifier = payload.get('sub')
    except jwt.InvalidTokenError:
        raise credentials_exception

    user = session.scalar(select(User).where(User.id == int_identifier))
    if user is None:
        raise credentials_exception
    return user


def verify_password(plain_password: str, hashed_password: str) -> tuple:
    return password_hash.verify_and_update(plain_password, hashed_password)


def get_hash(plain_text: str) -> str:
    return password_hash.hash(plain_text,)


def generate_token(data: dict, exp_time_delta: Optional[timedelta] = None):
    data_to_encode = data.copy()

    if not exp_time_delta:
        exp_time_delta = timedelta(minutes=15)

    expire = datetime.now(timezone.utc) + exp_time_delta
    data_to_encode['sub'] = str(data_to_encode['sub'])
    data_to_encode['exp'] = expire
    encoded_jwt = jwt.encode(
        data_to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def authenticate_user(
    session: Session, identity: str, password: str
) -> Optional[User]:
    user_db = session.scalar(
        select(User).where(
            (User.username == identity) | (User.email == identity)
        )
    )
    if not (user_db and verify_password(password, user_db.password)):
        return

    return user_db
