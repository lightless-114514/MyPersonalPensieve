import redis.asyncio as aioredis
from app.config import settings
from typing import Optional


class RedisService:
    def __init__(self):
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            self._redis = aioredis.from_url(
                f"redis://{settings.redis_host}:{settings.redis_port}",
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    KEY_MEMORIES_RECENT = "memories:recent"
    KEY_TASK_PREFIX = "task:"
    KEY_RATE_PREFIX = "rate:ask:"

    async def cache_recent_memories(self, json_str: str) -> None:
        try:
            r = await self._get_redis()
            await r.setex(self.KEY_MEMORIES_RECENT, 600, json_str)
        except Exception:
            pass

    async def get_recent_memories(self) -> Optional[str]:
        try:
            r = await self._get_redis()
            return await r.get(self.KEY_MEMORIES_RECENT)
        except Exception:
            return None

    async def evict_recent_memories(self) -> None:
        try:
            r = await self._get_redis()
            await r.delete(self.KEY_MEMORIES_RECENT)
        except Exception:
            pass

    async def add_task_step(self, task_id: str, step: str) -> None:
        r = await self._get_redis()
        key = f"{self.KEY_TASK_PREFIX}{task_id}"
        await r.rpush(key, step)
        await r.expire(key, 300)

    async def get_task_steps(self, task_id: str) -> list[str]:
        r = await self._get_redis()
        key = f"{self.KEY_TASK_PREFIX}{task_id}"
        return await r.lrange(key, 0, -1)

    async def clear_task(self, task_id: str) -> None:
        r = await self._get_redis()
        await r.delete(f"{self.KEY_TASK_PREFIX}{task_id}")

    async def is_rate_limited(self, ip: str) -> bool:
        try:
            r = await self._get_redis()
            key = f"{self.KEY_RATE_PREFIX}{ip}"
            count = await r.incr(key)
            if count == 1:
                await r.expire(key, 60)
            return count > 60
        except Exception:
            return False

    async def get_rate_count(self, ip: str) -> int:
        r = await self._get_redis()
        count = await r.get(f"{self.KEY_RATE_PREFIX}{ip}")
        return int(count) if count else 0

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None


redis_service = RedisService()
