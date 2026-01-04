# app/services/cache_service.py

import json
from typing import Any, Optional
from redis.asyncio import Redis
from app.core.config import settings

class CacheService:
    def __init__(self):
        self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def get(self, key: str) -> Optional[Any]:
        data = await self.redis.get(key)
        if data is None:
            return None
        return json.loads(data)

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        await self.redis.setex(key, ttl_seconds, json.dumps(value))

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)

    async def close(self):
        await self.redis.close()