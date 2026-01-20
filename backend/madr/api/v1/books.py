from http import HTTPStatus

from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from madr.api.utils import is_fk_violation, is_unique_violation
from madr.dependencies import ActiveUser, AnnotatedBookQueryParams
from madr.models.book import Book
from madr.schemas import Message
from madr.schemas.books import (
    ORDERABLE_FIELDS as BOOK_ORDERABLE_FIELDS,
)
from madr.schemas.books import (
    BookCreate,
    BookPublic,
    BookUpdate,
    PublicBooksPaginated,
)
from madr.types import DBSession

router = APIRouter(prefix='/books', tags=['books'])


@router.get(
    '/', status_code=HTTPStatus.OK, response_model=PublicBooksPaginated
)
async def read_books_by_filter(
    session: DBSession, query: AnnotatedBookQueryParams
):
    order_dir = query.order_dir
    year_from = query.year_from
    year_to = query.year_to

    order_column = BOOK_ORDERABLE_FIELDS[query.order_by]
    stmt = select(
        *BOOK_ORDERABLE_FIELDS.values(), func.count().over().label('total')
    )

    if year_from is not None:
        stmt = stmt.where(Book.year >= year_from)
    if year_to is not None:
        stmt = stmt.where(Book.year < year_to)
    if query.name and query.name.strip():
        stmt = stmt.where(Book.name.ilike(f'%{query.name.strip()}%'))
    if query.title and query.title.strip():
        stmt = stmt.where(Book.title.ilike(f'%{query.title.strip()}%'))

    stmt = (
        stmt
        .order_by(
            order_column.asc() if order_dir == 'asc' else order_column.desc()
        )
        .offset(query.offset)
        .limit(query.limit)
    )

    results = (await session.execute(stmt)).mappings().all()
    if len(results) != 0:
        total = results[0].get('total', 0)

        books = [BookPublic.model_validate(row) for row in results]
        return PublicBooksPaginated(
            data=books,
            page=query.page,
            total=total,
            has_prev=query.page > 1,
            has_next=(query.offset + query.limit) < total,
        )
    return PublicBooksPaginated(page=query.page)


@router.post('/', status_code=HTTPStatus.CREATED, response_model=BookPublic)
async def create_book(
    _: ActiveUser,
    input_book: BookCreate,
    session: DBSession,
):
    db_book = Book(**input_book.model_dump(exclude_unset=True))

    try:
        # ipdb.set_trace()
        session.add(db_book)
        await session.commit()
        await session.refresh(db_book)
    except IntegrityError as err:
        # ipdb.set_trace()
        await session.rollback()

        if is_fk_violation(err):
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Novelist not found',
            )
        # ipdb.set_trace()
        if is_unique_violation(err):
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Book already exists',
            )

        raise HTTPException(  # pragma: no cover
            status_code=HTTPStatus.CONFLICT,
            detail='Integrity violation',
        )
    except SQLAlchemyError:
        # ipdb.set_trace()
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Database error',
        )
    except Exception:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Internal error',
        )
    # ipdb.set_trace()
    return db_book


@router.put('/{book_id}', status_code=HTTPStatus.OK, response_model=BookPublic)
async def update_book(
    _: ActiveUser,
    book_id: int,
    input_book: BookUpdate,
    session: DBSession,
):
    existing_book = await session.scalar(
        select(Book).where(Book.id == book_id)
    )

    if not existing_book:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Book not found'
        )

    update_data = input_book.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(existing_book, key, value)

    try:
        await session.commit()
        await session.refresh(existing_book)
    except IntegrityError as err:
        await session.rollback()

        if is_fk_violation(err):
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Novelist not found',
            )

        if is_unique_violation(err):
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Book already exists',
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

    return existing_book


@router.get('/{book_id}', status_code=HTTPStatus.OK, response_model=BookPublic)
async def get_book(
    book_id: int,
    session: DBSession,
):
    existing_book = await session.scalar(
        select(Book).where(Book.id == book_id)
    )

    if not existing_book:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Book not found'
        )

    return existing_book


@router.delete('/{book_id}', status_code=HTTPStatus.OK, response_model=Message)
async def delete_book(
    _: ActiveUser,
    book_id: int,
    session: DBSession,
):
    try:
        result = await session.execute(delete(Book).where(Book.id == book_id))
        await session.commit()
        if result.rowcount == 0:  # type: ignore
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail='Book not found'
            )

    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Database error',
        )

    return {'message': 'Book Removed'}
