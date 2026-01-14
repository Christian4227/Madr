from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped, mapped_as_dataclass, mapped_column

from madr.models import table_registry
from madr.models.mixins import DateMixin


@mapped_as_dataclass(table_registry)
class User(DateMixin):
    __tablename__ = 'users'

    __table_args__ = (
        CheckConstraint(
            'char_length(username) > 0', name='ck_user_username_len'
        ),
        CheckConstraint(
            'char_length(password) >= 8', name='ck_user_password_len'
        ),
        CheckConstraint('char_length(email) >= 3', name='ck_user_email_len'),
        CheckConstraint(
            "position('@' in email) > 1", name='ck_user_email_has_at'
        ),
    )
    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
