from http import HTTPStatus

import ipdb  # noqa: F401
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from madr.dependecies import active_user, db_session
from madr.models.novelist import Novelist
from madr.schemas import Message
from madr.schemas.novelists import (
    NovelistPublic,
    NovelistSchema,
    NovelistUpdate,
)

router = APIRouter(prefix='/novelists', tags=['novelists'])


@router.post(
    '/', status_code=HTTPStatus.CREATED, response_model=NovelistPublic
)
def create_novelist(
    _: active_user,
    novelist: NovelistSchema,
    session: db_session,
):
    stmt = select(Novelist).where((Novelist.name == novelist.name))
    existing_novelist = session.scalar(stmt)
    if existing_novelist:
        raise HTTPException(
            HTTPStatus.CONFLICT, detail='Novelist already exists'
        )
    db_novelist = Novelist(**novelist.model_dump())
    session.add(db_novelist)
    session.commit()
    session.refresh(db_novelist)
    return db_novelist


@router.put(
    '/{novelist_id}', status_code=HTTPStatus.OK, response_model=NovelistPublic
)
def update_novelist(
    _: active_user,
    novelist_id: int,
    novelist: NovelistUpdate,
    session: db_session,
):
    # Get the novelist
    existing_novelist = session.scalar(
        select(Novelist).where(Novelist.id == novelist_id)
    )

    if not existing_novelist:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Novelist not found'
        )

    update_data = novelist.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(existing_novelist, key, value)

    try:
        session.commit()
        session.refresh(existing_novelist)
    except Exception:
        session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Failed to update novelist',
        )

    return existing_novelist


@router.delete(
    '/{novelist_id}', status_code=HTTPStatus.OK, response_model=Message
)
def remove_novelist(
    active_user: active_user,
    novelist_id: int,
    session: db_session,
):
    # Primeiro verifica se o novelist existe
    existing_novelist = session.scalar(
        select(Novelist).where(Novelist.id == novelist_id)
    )

    if not existing_novelist:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Novelist not found'
        )

    session.delete(existing_novelist)
    session.commit()

    return {'message': 'Novelist Removed'}
