from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from madr.core.database import get_session
from madr.core.security import get_hash
from madr.dependecies import active_user, db_session
from madr.models.user import User
from madr.schemas import Message
from madr.schemas.user import UserCreate, UserPublic, UserUpdate

router = APIRouter(prefix='/users', tags=['users'])


@router.post('/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    stmt = select(User)
    stmt.where((User.username == user.username) | (User.email == user.email))
    existing_user = session.scalar(stmt)
    if existing_user:
        raise HTTPException(
            HTTPStatus.CONFLICT, detail='Conta já consta no MADR'
        )
    db_user = User(**user.model_dump(exclude_unset=True, exclude={'password'}))
    db_user.password = get_hash(db_user.password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.put('/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
def udpate_user(
    active_user: active_user, user: UserUpdate, session: db_session
):

    existing_user = session.scalar(
        select(User).where(User.id == active_user.id)
    )
    if not existing_user:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail='User Not Found')
    items = user.model_dump(
        exclude_unset=True, exclude={'password': True}
    ).items()
    for key, value in items:
        setattr(existing_user, key, value)
    session.commit()
    session.refresh(existing_user)
    return existing_user


# @router.get(
#     '/',
#     status_code=HTTPStatus.OK,
#     response_model=UserList,
# )
# def read_users(
#     skip: int = 0, limit: int = 10, session: Session = Depends(get_session)
# ):
#     users = session.scalars(select(User).offset(skip).limit(limit)).all()

#     return {'users': users}


@router.delete('/', status_code=HTTPStatus.OK, response_model=Message)
def remove_user(
    active_user: active_user,
    session: Session = Depends(get_session),
):
    try:
        session.execute(delete(User).where(User.id == active_user.id))
        session.commit()
    except Exception:
        raise HTTPException(HTTPStatus.NOT_FOUND, 'User Not Found')
    return {'message': 'Account Removed'}
