from http import HTTPStatus  # noqa: I001

from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import ipdb  # noqa: F401
from madr.api.utils import is_fk_violation, is_unique_violation
from madr.dependecies import AnnotatedBookQueryParams, active_user, db_session
from madr.models.book import Book
from madr.schemas import Message
from madr.schemas.books import (
    ORDERABLE_FIELDS,
    BookCreate,
    BookPublic,
    BookUpdate,
    PublicBooksPaginated,
)

router = APIRouter(prefix='/books', tags=['books'])


# TODO:
# * busca por parte do nome ou titulo, e ano
@router.get(
    '/', status_code=HTTPStatus.OK, response_model=PublicBooksPaginated
)
def read_books_by_filter(session: db_session, query: AnnotatedBookQueryParams):
    order_dir = query.order_dir
    year_from = query.year_from
    year_to = query.year_to

    order_column = ORDERABLE_FIELDS[query.order_by]
    stmt = select(
        Book.id,
        Book.name,
        Book.title,
        Book.year,
        Book.created_at,
        func.count().over().label('total'),
    )

    if year_from is not None:
        stmt = stmt.where(Book.year >= year_from)
    if year_to is not None:
        stmt = stmt.where(Book.year < year_to)
    if query.name and query.name.strip():
        stmt = stmt.where(Book.name.ilike(f'%{query.name.strip()}%'))
    if query.title and query.title.strip():
        stmt = stmt.where(Book.title.ilike(f'%{query.title.strip()}%'))

    stmt = stmt.offset(query.offset)
    stmt = stmt.limit(query.limit)
    stmt = stmt.order_by(
        order_column.asc() if order_dir == 'asc' else order_column.desc()
    )

    results = session.execute(stmt).mappings().all()
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
    # ipdb.set_trace()
    return PublicBooksPaginated(page=query.page)


@router.post('/', status_code=HTTPStatus.CREATED, response_model=BookPublic)
def create_book(
    _: active_user,
    input_book: BookCreate,
    session: db_session,
):
    db_book = Book(**input_book.model_dump(exclude_unset=True))

    try:
        session.add(db_book)
        session.commit()
        session.refresh(db_book)
    except IntegrityError as err:
        session.rollback()

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

        raise HTTPException(  # pragma: no cover
            status_code=HTTPStatus.CONFLICT,
            detail='Integrity violation',
        )
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Database error',
        )
    except Exception:
        session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Internal error',
        )

    return db_book


@router.put('/{book_id}', status_code=HTTPStatus.OK, response_model=BookPublic)
def update_book(
    _: active_user,
    book_id: int,
    input_book: BookUpdate,
    session: db_session,
):
    existing_book = session.scalar(select(Book).where(Book.id == book_id))

    if not existing_book:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Book not found'
        )

    update_data = input_book.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(existing_book, key, value)

    try:
        session.commit()
        session.refresh(existing_book)
    except IntegrityError as err:
        session.rollback()

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
        session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Database error',
        )

    return existing_book


@router.get('/{book_id}', status_code=HTTPStatus.OK, response_model=BookPublic)
def get_book(
    book_id: int,
    session: db_session,
):
    existing_book = session.scalar(select(Book).where(Book.id == book_id))

    if not existing_book:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Book not found'
        )

    return existing_book


@router.delete('/{book_id}', status_code=HTTPStatus.OK, response_model=Message)
def delete_book(
    _: active_user,
    book_id: int,
    session: db_session,
):
    try:
        result = session.execute(delete(Book).where(Book.id == book_id))
        session.commit()
        if result.rowcount == 0:  # type: ignore
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail='Book not found'
            )

    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Database error',
        )

    return {'message': 'Book Removed'}
