from typing import List

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from madr.models.user import User


def test_create_user(session: Session):
    new_user = User(username='alice', password='secret', email='teste@test')

    session.add(new_user)
    session.commit()

    user = session.scalar(select(User).where(User.username == 'alice'))

    assert user is not None
    assert user.username == 'alice'


def test_update_user(session: Session, user: User):
    username = user.username
    user.username = f'modified_{username}'
    session.add(user)
    session.commit()

    user_modfied = session.scalar(select(User).where())
    assert user_modfied is not None
    assert user_modfied.username == f'modified_{username}'


def test_delete_user(session: Session, user: User):
    session.execute(delete(User).where(User.id == user.id))
    session.commit()

    deleted = session.scalar(select(User).where(User.id == user.id))
    assert deleted is None


def test_read_users(session: Session, users: List[User]):
    total_expected = 11
    finded_users = session.scalars(select(User).where()).all()
    assert finded_users is not None
    assert len(finded_users) == total_expected
