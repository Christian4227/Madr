from http import HTTPStatus

import ipdb  # noqa: F401
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from madr.dependecies import active_user, db_session
from madr.models.book import Book
from madr.schemas.books import BookCreate, BookDb

router = APIRouter(prefix='/books', tags=['users'])


def is_fk_violation(err: IntegrityError) -> bool:
    message = str(err.orig).lower()
    return 'foreign key' in message


def is_unique_violation(err: IntegrityError) -> bool:
    message = str(err.orig).lower()
    return 'unique constraint' in message


@router.post('/', status_code=HTTPStatus.CREATED, response_model=BookDb)
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

        raise HTTPException(  # pragma: no cover - TODO: add check constraints
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
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Internal error',
        )
    return db_book
