from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from typing import Annotated, Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from madr.config import Settings
from madr.core.database import get_session
from madr.core.redis import redis_manager
from madr.models.user import User
from madr.schemas.user import AuthContext

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')
settings = Settings()  # type: ignore


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuthContext:
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    credentials_expired = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Expired token',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    session_invalidated = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Session invalidated',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        int_identifier = int(payload.get('sub'))
        token_version = int(payload.get('ver', 0))
        jti = payload.get('jti')
        exp = payload.get('exp')

    except jwt.ExpiredSignatureError:
        raise credentials_expired
    except (jwt.DecodeError, jwt.InvalidTokenError, ValueError, TypeError):
        raise credentials_exception

    if await redis_manager.is_token_denyed_list(jti):
        raise session_invalidated

    user = await session.scalar(select(User).where(User.id == int_identifier))
    if user is None:
        raise credentials_exception

    # Check token version
    current_version = await redis_manager.get_user_token_version(user.id)
    if current_version != token_version:
        raise session_invalidated

    return AuthContext(
        current_user=user,
        jti=jti,
        exp=exp,
        ver=token_version,
    )


def verify_password(
    plain_password: str, hashed_password: str
) -> tuple[bool, bool]:
    is_valid, new_hash = password_hash.verify_and_update(
        plain_password, hashed_password
    )
    needs_rehash = new_hash is not None
    return (is_valid, needs_rehash)


def get_hash(plain_text: str) -> str:
    return password_hash.hash(plain_text)


def generate_token(data: dict, exp_time_delta: Optional[timedelta] = None):
    data_to_encode = data.copy()

    if not exp_time_delta:
        exp_time_delta = timedelta(minutes=15)

    expire = datetime.now(timezone.utc) + exp_time_delta
    data_to_encode['sub'] = str(data_to_encode['sub'])
    data_to_encode['exp'] = expire
    data_to_encode['iat'] = datetime.now(timezone.utc)
    encoded_jwt = jwt.encode(
        data_to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


@dataclass
class AuthResult:
    authenticated: bool
    user: Optional[User]
    needs_rehash: bool


async def authenticate_user(
    session: AsyncSession, identity: str, password: str
) -> AuthResult:
    auth_result = AuthResult(False, None, False)
    stmt = select(User).where(
        (User.username == identity) | (User.email == identity)
    )
    user_db = await session.scalar(stmt)
    if not user_db:
        return auth_result

    is_valid, needs_rehash = verify_password(password, user_db.password)

    if not is_valid:
        return auth_result
    return AuthResult(True, user_db, needs_rehash)
