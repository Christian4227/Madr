from typing import Generic, List, Literal, TypeVar

from pydantic import BaseModel, Field

T = TypeVar('T')


class Message(BaseModel):
    message: str


class PaginateOrderParams(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
    order_dir: Literal['desc', 'asc'] = 'desc'


class BookQueryParams(PaginateOrderParams):
    order_by: Literal['title', 'year', 'name', 'created_at', 'updated_at'] = (
        'created_at'
    )


class OutputPaginated(BaseModel, Generic[T]):
    data: List[T]
    total: int
    page: int
    has_prev: bool
    has_next: bool
