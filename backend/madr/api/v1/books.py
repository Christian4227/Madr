from http import HTTPStatus

import ipdb  # noqa: F401
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from sqlalchemy import select

from madr.dependecies import active_user, db_session
from madr.models.book import Book
from madr.schemas.books import BookCreate, BookDb

router = APIRouter(prefix='/books', tags=['users'])


@router.post('/', status_code=HTTPStatus.CREATED, response_model=BookDb)
def create_book(
    active_user: active_user, input_book: BookCreate, session: db_session
):
    stmt = select(Book)
    stmt = stmt.where(Book.name == input_book.name)
    existing_book = session.scalar(stmt)
    ipdb.set_trace()
    if existing_book:
        raise HTTPException(HTTPStatus.CONFLICT, detail='Book has been exists')
    db_book = Book(**input_book.model_dump(exclude_unset=True))

    try:
        session.add(db_book)
        session.commit()
        session.refresh(db_book)
    except Exception:
        session.rollback()
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail='Failed to create book',
        )
    return db_book
