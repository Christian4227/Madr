from http import HTTPStatus

from fastapi import APIRouter

from madr.schemas.user import UserCreate, UserDB, UserList, UserPublic

router = APIRouter(prefix='/users', tags=['users'])

fake_database = []


@router.post('/', status_code=HTTPStatus.CREATED, response_model=UserPublic)
def create_user(user: UserCreate):
    next_id = len(fake_database) + 1
    user_with_id = UserDB(**user.model_dump(), id=next_id)
    fake_database.append(user_with_id)
    return user_with_id


@router.get('/', status_code=HTTPStatus.OK, response_model=UserList)
def read_users():
    return {'users': fake_database}
