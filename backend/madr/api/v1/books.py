from http import HTTPStatus

from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from madr.api.utils import is_fk_violation, is_unique_violation
from madr.dependecies import active_user, db_session
from madr.models.book import Book
from madr.schemas import Message
from madr.schemas.books import BookCreate, BookPublic, BookUpdate

router = APIRouter(prefix='/books', tags=['books'])  # ✅ 'books' não 'users'


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
    except Exception:  # ✅ Mantido para coverage, mas não é ideal
        session.rollback()  # ✅ Adicione rollback aqui também
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

    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail='Cannot delete book with existing references',
        )
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Database error',
        )

    return {'message': 'Book Removed'}


# TODO
# - delete book
# - obter book por id
