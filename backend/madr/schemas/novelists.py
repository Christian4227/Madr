from typing import List, Optional

from pydantic import BaseModel

from madr.schemas.books import BookPublic
from madr.schemas.mixins import DateSchema


class NovelistBase(BaseModel):
    name: str


class NovelistSchema(NovelistBase): ...


class NovelistUpdate(BaseModel):
    name: Optional[str] = None


class NovelistPublic(NovelistBase):
    id: int


class NovelistDB(NovelistBase, DateSchema):
    id: int
    books: List[BookPublic]
    model_config = {'from_attributes': True}


class NovelistList(BaseModel):
    items: List[NovelistPublic]
