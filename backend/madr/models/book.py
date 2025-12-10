from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    Mapped,
    mapped_as_dataclass,
    mapped_column,
    relationship,
)

from madr.models import table_registry
from madr.models.mixins import DateMixin

if TYPE_CHECKING:
    from madr.models.novelist import Novelist


@mapped_as_dataclass(table_registry)
class Book(DateMixin):
    __tablename__ = 'books'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    year: Mapped[str] = mapped_column()
    title: Mapped[str] = mapped_column()

    id_novelist: Mapped[int] = mapped_column(ForeignKey('novelists.id'))

    novelist: Mapped[Novelist] = relationship(back_populates='books')
