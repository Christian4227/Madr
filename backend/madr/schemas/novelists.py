from typing import List, Literal, Optional

from pydantic import BaseModel

from madr.models.novelist import Novelist
from madr.schemas import OutputPaginated, PaginateOrderParams
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


class NovelistQueryParams(PaginateOrderParams):
    name: Optional[str] = None
    order_by: Literal['id', 'name'] = 'id'


PublicNovelistsPaginated = OutputPaginated[NovelistPublic]
ORDERABLE_FIELDS = {'id': Novelist.id, 'name': Novelist.name}
