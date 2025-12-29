from typing import Generic, List, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, computed_field
from pydantic.alias_generators import to_camel

T = TypeVar('T')


class Message(BaseModel):
    message: str


class PaginateParams(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)

    @computed_field
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginateOrderParams(PaginateParams):
    order_dir: Literal['desc', 'asc'] = 'desc'


class OutputPaginated(BaseModel, Generic[T]):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    data: List[T] = []
    total: int = 0
    page: int
    has_prev: bool = False
    has_next: bool = False
