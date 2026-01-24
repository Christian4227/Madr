from datetime import datetime, timezone
from typing import Optional

from redis.asyncio import Redis

from madr.config import Settings

settings = Settings()  # type: ignore


class __RedisManager:
    def __init__(self):
        self.redis: Optional[Redis] = None

    async def connect(self):
        self.redis = await Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True,
        )

    async def close(self):
        if self.redis:
            await self.redis.close()

    async def deny_token(self, jti: str, exp: int):
        """Adiciona Token na lista de negação com TTL"""
        ttl = exp - int(datetime.now(tz=timezone.utc).timestamp())
        if self.redis and ttl > 0:
            await self.redis.setex(f'deny:token:{jti}', ttl, '1')

    async def is_token_denyed_list(self, jti: str) -> bool:
        """Verifica se o token esta na lista de negação"""
        if not self.redis:
            return False
        return await self.redis.exists(f'deny:token:{jti}') > 0  # type: ignore

    async def increment_user_token_version(self, user_id: int) -> int:
        """Logout de todos dispositivos"""
        new_version = await self.redis.incr(f'user:token_version:{user_id}')  # type: ignore
        return new_version

    async def get_user_token_version(self, user_id: int) -> int:
        """Obter versão atual to token do ususário"""
        version = await self.redis.get(f'user:token_version:{user_id}')  # type: ignore
        return int(version) if version else 0


redis_manager = __RedisManager()
