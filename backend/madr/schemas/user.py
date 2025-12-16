from typing import List, Optional

from pydantic import BaseModel, EmailStr

from madr.schemas.mixins import DateSchema


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None


class UserPublic(UserBase):
    id: int


class UserDB(UserPublic, DateSchema):
    model_config = {'from_attributes': True}


class UserList(BaseModel):
    users: List[UserPublic]
