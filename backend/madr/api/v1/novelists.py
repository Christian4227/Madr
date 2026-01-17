from http import HTTPStatus

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from madr.api.utils import is_unique_violation
from madr.dependecies import (
    AnnotatedBookQueryParams,
    AnnotatedNovelistQueryParams,
    active_user,
    db_session,
)
from madr.models.book import Book
from madr.models.novelist import Novelist
from madr.schemas import Message
from madr.schemas.books import (
    ORDERABLE_FIELDS as BOOK_ORDERABLE_FIELDS,
)
from madr.schemas.books import (
    BookPublic,
    PublicBooksPaginated,
)
from madr.schemas.novelists import (
    ORDERABLE_FIELDS as NOVELIST_ORDERABLE_FIELDS,
)
from madr.schemas.novelists import (
    NovelistPublic,
    NovelistSchema,
    NovelistUpdate,
    PublicNovelistsPaginated,
)

router = APIRouter(prefix='/novelists', tags=['novelists'])


@router.get(
    '/', status_code=HTTPStatus.OK, response_model=PublicNovelistsPaginated
)
async def read_novelists_by(
    session: db_session, query: AnnotatedNovelistQueryParams
):
    offset = query.offset
    order_by = query.order_by
    order_dir = query.order_dir
    page = query.page
    limit = query.limit
    order_column = NOVELIST_ORDERABLE_FIELDS[order_by]

    stmt = select(
        *NOVELIST_ORDERABLE_FIELDS.values(),
        func.count().over().label('total'),
    )

    if query.name and query.name.strip():
        stmt = stmt.where(Novelist.name.ilike(f'%{query.name.strip()}%'))

    stmt = (
        stmt
        .order_by(
            order_column.asc() if order_dir == 'asc' else order_column.desc()
        )
        .offset(offset)
        .limit(limit)
    )

    results = (await session.execute(stmt)).mappings().all()
    if len(results) == 0:
        return PublicNovelistsPaginated(page=query.page)

    total = results[0]['total']

    data = [NovelistPublic.model_validate(novelist) for novelist in results]

    return PublicNovelistsPaginated(
        data=data,
        page=page,
        total=total,
        has_prev=page > 1,
        has_next=(offset + limit) < total,
    )


@router.post(
    '/', status_code=HTTPStatus.CREATED, response_model=NovelistPublic
)
async def create_novelist(
    _: active_user,
    novelist: NovelistSchema,
    session: db_session,
):
    db_novelist = Novelist(**novelist.model_dump())

    try:
        session.add(db_novelist)
        await session.commit()
        await session.refresh(db_novelist)
    except IntegrityError as err:
        await session.rollback()
        if is_unique_violation(err):
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Novelist already exists',
            )
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Database error',
        )
    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Database error',
        )

    return db_novelist


@router.put(
    '/{novelist_id}', status_code=HTTPStatus.OK, response_model=NovelistPublic
)
async def update_novelist(
    _: active_user,
    novelist_id: int,
    novelist: NovelistUpdate,
    session: db_session,
):
    existing_novelist = await session.scalar(
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
        await session.commit()
        await session.refresh(existing_novelist)
    except IntegrityError as err:
        await session.rollback()
        if is_unique_violation(err):
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Novelist already exists',
            )
    return existing_novelist


@router.delete(
    '/{novelist_id}', status_code=HTTPStatus.OK, response_model=Message
)
async def remove_novelist(
    _: active_user,
    novelist_id: int,
    session: db_session,
):

    existing_novelist = await session.scalar(
        select(Novelist).where(Novelist.id == novelist_id)
    )

    if not existing_novelist:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Novelist not found'
        )

    await session.delete(existing_novelist)
    await session.commit()

    return {'message': 'Novelist Removed'}


@router.get(
    '/{novelist_id}/books',
    status_code=HTTPStatus.OK,
    response_model=PublicBooksPaginated,
)
async def get_books_by_novelist(
    novelist_id: int, query: AnnotatedBookQueryParams, session: db_session
):
    offset = query.offset

    order_field = BOOK_ORDERABLE_FIELDS[query.order_by]

    stmt = (
        select(
            Book.id,
            Book.title,
            Book.name,
            Book.year,
            func.count().over().label('total'),
        )
        .where(Book.id_novelist == novelist_id)
        .order_by(
            order_field.desc()
            if query.order_dir == 'desc'
            else order_field.asc()
        )
        .offset(offset)
        .limit(query.limit)
    )

    books = (await session.execute(stmt)).mappings().all()

    total_books = books[0]['total'] if books else 0
    data_books = [BookPublic(**b) for b in books]

    return PublicBooksPaginated(
        page=query.page,
        data=data_books,
        total=total_books,
        has_prev=query.page > 1,
        has_next=(offset + query.limit) < total_books,
    )
