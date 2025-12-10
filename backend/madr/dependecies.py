from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.orm import Session

from madr.core.database import get_session
from madr.core.security import get_current_user
from madr.schemas.user import UserPublic


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int


request_form_data = Annotated[OAuth2PasswordRequestForm, Depends()]

db_session = Annotated[Session, Depends(get_session)]

active_user = Annotated[UserPublic, Depends(get_current_user)]
