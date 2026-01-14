from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint
from sqlalchemy.orm import (
    Mapped,
    mapped_as_dataclass,
    mapped_column,
    relationship,
)

from madr.models import table_registry
from madr.models.mixins import DateMixin

if TYPE_CHECKING:
    from madr.models.book import Book


@mapped_as_dataclass(table_registry)
class Novelist(DateMixin):
    __tablename__ = 'novelists'
    __table_args__ = (
        CheckConstraint('char_length(name) > 0', name='ck_novelist_name_len'),
    )
    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    books: Mapped[list[Book]] = relationship(
        init=False,
        cascade='all, delete-orphan',
        lazy='selectin',
        back_populates='novelist',
    )

    def __init__(self, name: str):
        self.name = name
