from http import HTTPStatus

import ipdb  # noqa: F401
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from madr.core.database import get_session
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
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    stmt = select(User)
    stmt = stmt.where(
        (User.username == user.username) | (User.email == user.email)
    )

    existing_user = session.scalar(stmt)
    if existing_user:
        raise HTTPException(HTTPStatus.CONFLICT, detail='User alredy exists')
    db_user = User(**user.model_dump(exclude_unset=True))
    db_user.password = get_hash(db_user.password)
    try:
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
    except Exception:
        session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Failed to create user',
        )

    return db_user


@router.put('/', status_code=HTTPStatus.OK, response_model=UserPublic)
def update_user(
    active_user: active_user, user: UserUpdate, session: db_session
):

    update_data = user.model_dump(
        exclude_unset=True, exclude={'password': True}
    )
    for key, value in update_data.items():
        setattr(active_user, key, value)
    try:
        session.commit()
        session.refresh(active_user)
    except Exception:
        session.rollback()
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
def read_users(
    skip: int = 0, limit: int = 10, session: Session = Depends(get_session)
):
    users = session.scalars(select(User).offset(skip).limit(limit)).all()

    return {'users': users}


@router.delete('/', status_code=HTTPStatus.OK, response_model=Message)
def remove_user(
    active_user: active_user,
    session: Session = Depends(get_session),
):
    session.execute(delete(User).where(User.id == active_user.id))
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Failed to delete user',
        )

    return {'message': 'Account Removed'}
