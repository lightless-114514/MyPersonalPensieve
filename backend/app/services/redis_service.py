"""内存缓存实现，替代 Redis。

保留与原 redis_service 相同的方法签名，业务层无需改动。
特性：
- 字符串缓存 + TTL 过期
- 列表（用于任务步骤）
- 计数器（用于限流）
"""
import asyncio
import time
from typing import Optional


class _MemoryStore:
    """简单的内存存储，支持 TTL。"""

    def __init__(self):
        self._data: dict[str, tuple[any, float | None]] = {}
        self._lists: dict[str, list[tuple[any, float | None]]] = {}
        self._lock = asyncio.Lock()

    def _is_expired(self, expire_at: float | None) -> bool:
        return expire_at is not None and time.time() > expire_at

    async def setex(self, key: str, ttl: int, value: any) -> None:
        async with self._lock:
            self._data[key] = (value, time.time() + ttl)

    async def get(self, key: str) -> Optional[any]:
        async with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            value, expire_at = entry
            if self._is_expired(expire_at):
                del self._data[key]
                return None
            return value

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._data.pop(key, None)
            self._lists.pop(key, None)

    async def rpush(self, key: str, value: any, ttl: int | None = None) -> None:
        async with self._lock:
            if key not in self._lists:
                self._lists[key] = []
            expire_at = time.time() + ttl if ttl else None
            self._lists[key].append((value, expire_at))

    async def lrange(self, key: str, start: int, end: int) -> list[any]:
        async with self._lock:
            items = self._lists.get(key, [])
            # 过滤过期项
            now = time.time()
            valid = [(v, e) for v, e in items if e is None or now <= e]
            if len(valid) != len(items):
                self._lists[key] = valid
            values = [v for v, _ in valid]
            if end == -1:
                end = len(values)
            return values[start:end]

    async def incr(self, key: str, ttl: int | None = None) -> int:
        async with self._lock:
            entry = self._data.get(key)
            if entry is None or self._is_expired(entry[1]):
                count = 0
            else:
                count = int(entry[0]) if entry[0] is not None else 0
            count += 1
            expire_at = time.time() + ttl if ttl else (entry[1] if entry and entry[1] else None)
            self._data[key] = (count, expire_at)
            return count


class RedisService:
    """内存版 RedisService，接口与原版兼容。"""

    def __init__(self):
        self._store = _MemoryStore()

    KEY_MEMORIES_RECENT = "memories:recent"
    KEY_TASK_PREFIX = "task:"
    KEY_RATE_PREFIX = "rate:ask:"

    async def cache_recent_memories(self, json_str: str) -> None:
        try:
            await self._store.setex(self.KEY_MEMORIES_RECENT, 600, json_str)
        except Exception:
            pass

    async def get_recent_memories(self) -> Optional[str]:
        try:
            return await self._store.get(self.KEY_MEMORIES_RECENT)
        except Exception:
            return None

    async def evict_recent_memories(self) -> None:
        try:
            await self._store.delete(self.KEY_MEMORIES_RECENT)
        except Exception:
            pass

    async def add_task_step(self, task_id: str, step: str) -> None:
        key = f"{self.KEY_TASK_PREFIX}{task_id}"
        await self._store.rpush(key, step, ttl=300)

    async def get_task_steps(self, task_id: str) -> list[str]:
        key = f"{self.KEY_TASK_PREFIX}{task_id}"
        return await self._store.lrange(key, 0, -1)

    async def clear_task(self, task_id: str) -> None:
        await self._store.delete(f"{self.KEY_TASK_PREFIX}{task_id}")

    async def is_rate_limited(self, ip: str) -> bool:
        try:
            key = f"{self.KEY_RATE_PREFIX}{ip}"
            count = await self._store.incr(key, ttl=60)
            return count > 60
        except Exception:
            return False

    async def get_rate_count(self, ip: str) -> int:
        v = await self._store.get(f"{self.KEY_RATE_PREFIX}{ip}")
        return int(v) if v else 0

    async def close(self) -> None:
        # 内存版无需关闭
        pass


redis_service = RedisService()
