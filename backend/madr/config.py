from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / '.env', env_file_encoding='utf-8'
    )

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    CORS_ORIGINS: list[str]

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(',')]
        return v
