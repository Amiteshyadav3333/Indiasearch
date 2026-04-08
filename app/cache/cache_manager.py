import json
import time
import logging
from collections import OrderedDict
from typing import Any, Optional
from app.cache.redis_client import RedisClient

logger = logging.getLogger(__name__)

SEARCH_TTL  = 300
WEATHER_TTL = 600
CRICKET_TTL = 30
AI_TTL      = 1800
FINANCE_TTL = 60

class _MemoryCache:
    """Simple TTL-aware in-memory cache fallback."""
    MAX_SIZE = 1000

    def __init__(self):
        self._store: OrderedDict[str, tuple] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        if key not in self._store:
            return None
        value, expires_at = self._store[key]
        if expires_at and time.time() > expires_at:
            del self._store[key]
            return None
        self._store.move_to_end(key)
        return value

    def set(self, key: str, value: Any, ttl: int = SEARCH_TTL) -> None:
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = (value, time.time() + ttl if ttl else None)
        if len(self._store) > self.MAX_SIZE:
            self._store.popitem(last=False)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def keys_with_prefix(self, prefix: str) -> list:
        return [k for k in self._store if k.startswith(prefix)]

_mem_cache = _MemoryCache()


class CacheManager:
    """High-level cache with Redis primary and in-memory fallback."""

    @staticmethod
    def get(key: str) -> Optional[Any]:
        try:
            client = RedisClient.get_client()
            if client:
                raw = client.get(key)
                return json.loads(raw) if raw else None
        except Exception as e:
            logger.warning(f"[Cache] Redis GET error: {e}")
        return _mem_cache.get(key)

    @staticmethod
    def set(key: str, value: Any, ttl: int = SEARCH_TTL) -> None:
        try:
            client = RedisClient.get_client()
            if client:
                client.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.warning(f"[Cache] Redis SET error: {e}")
        _mem_cache.set(key, value, ttl)

    @staticmethod
    def delete(key: str) -> None:
        try:
            client = RedisClient.get_client()
            if client:
                client.delete(key)
        except Exception:
            pass
        _mem_cache.delete(key)

    @staticmethod
    def invalidate_prefix(prefix: str) -> int:
        count = 0
        try:
            client = RedisClient.get_client()
            if client:
                keys = client.keys(f"{prefix}*")
                if keys:
                    count = client.delete(*keys)
        except Exception:
            pass
        mem_keys = _mem_cache.keys_with_prefix(prefix)
        for k in mem_keys:
            _mem_cache.delete(k)
        count += len(mem_keys)
        return count

    @staticmethod
    def make_key(*parts) -> str:
        return ":".join(str(p).lower().strip() for p in parts)
