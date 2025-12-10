from typing import List

from pydantic import BaseModel

from madr.schemas.books import BookPublic
from madr.schemas.mixins import DateSchema


class NovelistBase(BaseModel):
    name: str


class NovelistSchema(NovelistBase): ...


class NovelistPublic(NovelistBase):
    id: int


class NovelistDB(NovelistBase, DateSchema):
    id: int
    books: List[BookPublic]
    model_config = {'from_attributes': True}


class NovelistList(BaseModel):
    items: List[NovelistPublic]


# @mapped_as_dataclass(table_registry)
# class Novelist(DateMixin):
#     __tablename__ = 'novelists'
#     id: Mapped[int] = mapped_column(init=False, primary_key=True)
#     name: Mapped[str] = mapped_column(unique=True)
#     books: Mapped[List[Book]] = relationship(back_populates='novelist')
