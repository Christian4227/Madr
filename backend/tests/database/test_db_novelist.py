# from typing import List

# from sqlalchemy import delete, select
from sqlalchemy import select
from sqlalchemy.orm import Session

from madr.models.novelist import Novelist


def test_create_novelist(session: Session):
    new_novelist = Novelist(name='alice')

    session.add(new_novelist)
    session.commit()

    novelist = session.scalar(select(Novelist).where(Novelist.name == 'alice'))

    assert novelist is not None
    assert novelist.name == 'alice'


def test_update_novelist(session: Session, novelist: Novelist):
    name = novelist.name
    novelist.name = f'modified_{name}'
    session.add(novelist)
    session.commit()

    novelist_modfied = session.scalar(select(Novelist).where())
    assert novelist_modfied is not None
    assert novelist_modfied.name == f'modified_{name}'


# def test_delete_user(session: Session, user: User):
#     session.execute(delete(User).where(User.id == user.id))
#     session.commit()

#     deleted = session.scalar(select(User).where(User.id == user.id))
#     assert deleted is None


# def test_read_users(session: Session, users: List[User]):
#     total_expected = 11
#     finded_users = session.scalars(select(User).where()).all()
#     assert finded_users is not None
#     assert len(finded_users) == total_expected
