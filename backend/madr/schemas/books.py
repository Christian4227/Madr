from typing import List

from pydantic import BaseModel

from madr.models.novelist import Novelist
from madr.schemas.mixins import DateSchema


class BaseBook(BaseModel):
    name: str
    year: str
    title: str


class BookCreate(BaseBook):
    id_novelist: int


class BookPublic(BaseModel):
    id: int
    title: str
    model_config = {'from_attributes': True}


class BookDb(DateSchema, BookCreate):
    id: int
    novelist: Novelist
    model_config = {'from_attributes': True}


class BookList(BaseModel):
    items: List[BookPublic]
