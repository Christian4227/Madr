from typing import Awaitable, Callable, Optional

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from madr.models.novelist import Novelist


@pytest.mark.asyncio
async def test_create_novelist(session: AsyncSession):
    new_novelist = Novelist(name='alice')

    session.add(new_novelist)
    await session.commit()
    stmt = select(Novelist).where(Novelist.name == 'alice')
    novelist = await session.scalar(stmt)

    assert novelist is not None
    assert novelist.name == 'alice'


@pytest.mark.asyncio
async def test_create_novelist_deve_falhar_por_nome_curto(
    session: AsyncSession,
):
    new_novelist = Novelist(name='')
    session.add(new_novelist)
    with pytest.raises(IntegrityError, match='ck_novelist_name_len'):
        await session.commit()


@pytest.mark.asyncio
async def test_novelist_update(
    session: AsyncSession,
    novelist_with_books: Callable[
        [int, Optional[str], Optional[str]], Awaitable[Novelist]
    ],
):
    novelist = await novelist_with_books(35, None, None)
    name = novelist.name
    novelist_identifier = novelist.id
    novelist.name = f'modified_{name}'
    session.add(novelist)
    await session.commit()

    stmt = select(Novelist).where(Novelist.id == novelist_identifier)
    novelist_modified = await session.scalar(stmt)
    assert novelist_modified is not None
    assert novelist_modified.name == f'modified_{name}'
