from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_ignore_empty=True,
        extra='ignore',
    )
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    CORS_ORIGINS: str  # ← trocar de list[str] para str

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS to list"""
        if self.CORS_ORIGINS.startswith('['):
            import json  # noqa: PLC0415

            return json.loads(self.CORS_ORIGINS)
        return [x.strip() for x in self.CORS_ORIGINS.split(',')]
