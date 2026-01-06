from http import HTTPStatus

from fastapi import APIRouter, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from madr.api.utils import is_unique_violation
from madr.core.security import get_hash
from madr.dependecies import active_user, db_session
from madr.models.user import User
from madr.schemas import Message
from madr.schemas.user import (
    UserCreate,
    UserList,
    UserPublic,
    UserUpdate,
)

router = APIRouter(prefix='/users', tags=['users'])


@router.post('/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
async def create_user(user: UserCreate, session: db_session):
    db_user = User(**user.model_dump(exclude_unset=True))
    db_user.password = get_hash(db_user.password)
    try:
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
    except IntegrityError as err:
        await session.rollback()

        if is_unique_violation(err):
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='User already exists',
            )
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Database error',
        )
    return db_user


@router.put('/', status_code=HTTPStatus.OK, response_model=UserPublic)
async def update_user(
    active_user: active_user, user: UserUpdate, session: db_session
):

    update_data = user.model_dump(
        exclude_unset=True, exclude={'password': True}
    )
    for key, value in update_data.items():
        setattr(active_user, key, value)
    try:
        await session.commit()
        await session.refresh(active_user)
    except Exception:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Failed to update user',
        )
    return active_user


@router.get(
    '/',
    status_code=HTTPStatus.OK,
    response_model=UserList,
)
async def read_users(
    session: db_session,
    skip: int = 0,
    limit: int = 10,
):  # pragma: no cover

    result = await session.scalars(select(User).offset(skip).limit(limit))
    users = result.all()

    return {'users': users}


@router.delete('/', status_code=HTTPStatus.OK, response_model=Message)
async def remove_user(
    active_user: active_user,
    session: db_session,
):
    await session.execute(delete(User).where(User.id == active_user.id))
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Cannot delete account with existing references',
        )

    return {'message': 'Account Removed'}
