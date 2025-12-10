from typing import List

from pydantic import BaseModel

from madr.models.novelist import Novelist
from madr.schemas.mixins import DateSchema


class BaseBook(BaseModel):
    name: str
    year: str
    title: str


class BookSchema(BaseBook): ...


class BookPublic(BaseModel):
    id: int
    title: str
    model_config = {'from_attributes': True}


class DbBook(DateSchema, BaseModel):
    id: int
    id_novelist: int
    novelist: Novelist
    model_config = {'from_attributes': True}


class BookList(BaseModel):
    items: List[BookPublic]
