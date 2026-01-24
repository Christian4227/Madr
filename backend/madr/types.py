# madr/types.py
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from madr.core.database import get_session

DBSession = Annotated[AsyncSession, Depends(get_session)]
