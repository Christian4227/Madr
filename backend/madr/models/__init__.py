from sqlalchemy.orm import registry

table_registry = registry()

from madr.models.book import Book  # noqa: E402, F401
from madr.models.novelist import Novelist  # noqa: E402, F401
from madr.models.user import User  # noqa: E402, F401
