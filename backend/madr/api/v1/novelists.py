from http import HTTPStatus

import ipdb  # noqa: F401
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from madr.dependecies import active_user, db_session
from madr.models.novelist import Novelist
from madr.schemas.novelists import NovelistPublic, NovelistSchema

router = APIRouter(prefix='/novelists', tags=['novelists'])


@router.post(
    '/', status_code=HTTPStatus.CREATED, response_model=NovelistPublic
)
def create_novelist(
    current_user: active_user,
    novelist: NovelistSchema,
    session: db_session,
):
    stmt = select(Novelist).where((Novelist.name == novelist.name))
    existing_novelist = session.scalar(stmt)
    if existing_novelist:
        raise HTTPException(HTTPStatus.CONFLICT, detail='Novelist exists')
    db_novelist = Novelist(**novelist.model_dump())
    session.add(db_novelist)
    session.commit()
    session.refresh(db_novelist)
    return db_novelist


# @router.put(
#     '/{user_id}', status_code=HTTPStatus.CREATED, response_model=UserPublic
# )
# def udpate_user(
#     user_id: int, user: UserCreate, session: Session = Depends(get_session)
# ):
#     existing_user = session.scalar(select(User).where(User.id == user_id))
#     if not existing_user:
#         raise HTTPException(HTTPStatus.NOT_FOUND, detail='User Not Found')
#     items = user.model_dump(
#         exclude_unset=True, exclude={'password': True}
#     ).items()
#     for key, value in items:
#         setattr(existing_user, key, value)
#     session.commit()
#     session.refresh(existing_user)
#     return existing_user


# # @router.get(
# #     '/',
# #     status_code=HTTPStatus.OK,
# #     response_model=UserList,
# # )
# # def read_users(
# #     skip: int = 0, limit: int = 10, session: Session = Depends(get_session)
# # ):
# #     users = session.scalars(select(User).offset(skip).limit(limit)).all()

# #     return {'users': users}


# @router.delete('/', status_code=HTTPStatus.OK, response_model=Message)
# def remove_user(
#     current_user: Annotated[UserPublic, Depends(get_current_user)],
#     session: Session = Depends(get_session),
# ):
#     try:

#         session.execute(delete(User).where(User.id == current_user.id))
#         session.commit()
#     except Exception:

#         raise HTTPException(HTTPStatus.NOT_FOUND, 'User Not Found')
#     return {'message': 'Account Removed'}
