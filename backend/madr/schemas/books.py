from typing import List

from pydantic import BaseModel, Field

from madr.api.utils import optional_model
from madr.models.novelist import Novelist
from madr.schemas.mixins import DateSchema


class BaseBook(BaseModel):
    name: str
    year: str
    title: str


class BookCreate(BaseBook):
    model_config = {'populate_by_name': True}
    id_novelist: int = Field(alias='idNovelist')


class BookPublic(BaseModel):
    id: int
    title: str
    model_config = {'from_attributes': True}


@optional_model
class BookUpdate(BookCreate):
    pass


class BookDb(DateSchema, BookCreate):
    id: int
    novelist: Novelist
    model_config = {'from_attributes': True}


class BookList(BaseModel):
    items: List[BookPublic]
