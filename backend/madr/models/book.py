from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey
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
    __table_args__ = (
        CheckConstraint('char_length(name) > 0', name='ck_book_name_len'),
        CheckConstraint('char_length(title) > 0', name='ck_book_title_len'),
    )
    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    year: Mapped[int] = mapped_column(index=True, nullable=False)
    title: Mapped[str] = mapped_column()

    id_novelist: Mapped[int] = mapped_column(
        ForeignKey('novelists.id', ondelete='CASCADE')
    )

    novelist: Mapped[Novelist] = relationship(
        init=False, back_populates='books'
    )
