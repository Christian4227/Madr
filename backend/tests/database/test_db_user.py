from typing import List

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from madr.models.user import User


@pytest.mark.asyncio
async def test_create_user(session: AsyncSession):
    new_user = User(username='alice', password='secret', email='teste@test')

    session.add(new_user)
    await session.commit()

    user = await session.scalar(select(User).where(User.username == 'alice'))

    assert user is not None
    assert user.username == 'alice'


@pytest.mark.asyncio
async def test_update_user(session: AsyncSession, user: User):
    username = user.username
    user.username = f'modified_{username}'
    session.add(user)
    await session.commit()

    user_modfied = await session.scalar(select(User).where())
    assert user_modfied is not None
    assert user_modfied.username == f'modified_{username}'


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_delete_user(session: AsyncSession, user: User):
    await session.execute(delete(User).where(User.id == user.id))
    await session.commit()

    deleted = await session.scalar(select(User).where(User.id == user.id))
    assert deleted is None


@pytest.mark.asyncio
async def test_read_users(session: AsyncSession, users: List[User]):
    total_expected = 11
    finded_users = (await session.scalars(select(User).where())).all()
    assert finded_users is not None
    assert len(finded_users) == total_expected
