from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from madr.models.book import Book
from madr.models.novelist import Novelist
from madr.schemas import OutputPaginated, PaginateOrderParams
from madr.schemas.mixins import DateSchema

ORDERABLE_FIELDS: Dict[str, Any] = {
    'id': Book.id,
    'name': Book.name,
    'title': Book.title,
    'year': Book.year,
    'created_at': Book.created_at,
}


class BaseBook(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str
    year: int
    title: str


class BookCreate(BaseBook):
    id_novelist: int  # pode ser "id_novelist" ou "idNovelist"


class BookPublic(BaseBook):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: int


class BookUpdate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    title: Optional[str] = None
    name: Optional[str] = None
    year: Optional[int] = None
    id_novelist: Optional[int] = None


class BookDb(DateSchema, BookCreate):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

    id: int
    novelist: Novelist


class BookQueryParams(PaginateOrderParams):
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    name: Optional[str] = None
    title: Optional[str] = None
    order_by: Literal[
        'id', 'title', 'year', 'name', 'created_at', 'updated_at'
    ] = 'id'


PublicBooksPaginated = OutputPaginated[BookPublic]
