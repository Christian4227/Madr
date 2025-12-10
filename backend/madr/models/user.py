from sqlalchemy.orm import Mapped, mapped_as_dataclass, mapped_column

from madr.models import table_registry
from madr.models.mixins import DateMixin


@mapped_as_dataclass(table_registry)
class User(DateMixin):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
