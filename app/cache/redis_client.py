# app/cache/redis_client.py
# ⚡ Redis Connection — Singleton Client
# ----------------------------------------
# Provides a single shared Redis connection pool.
#
# Required env: REDIS_URL (e.g. redis://localhost:6379/0)
#               Set in .env → loaded by app/config/settings.py

import redis
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class RedisClient:
    """Singleton Redis connection pool wrapper."""

    _client: Optional[redis.Redis] = None

    @classmethod
    def get_client(cls) -> Optional[redis.Redis]:
        """
        Return the shared Redis client (lazy singleton).
        Uses connection pooling for production safety.
        """
        if cls._client is None:
            # First look for REDIS_URL in env directly, fallback to empty string
            url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            try:
                cls._client = redis.from_url(
                    url,
                    decode_responses=True,        # Return strings, not bytes
                    max_connections=20,           # Connection pool size
                    socket_connect_timeout=5,     # Fail fast if Redis is down
                    socket_timeout=5              # Operation timeout
                )
                cls._client.ping()                # Early health check
                logger.info(f"[Redis] Connected to: {url}")
            except Exception as e:
                logger.error(f"[Redis] Connection to {url} failed: {e}")
                cls._client = None                # Ensure it remains None if connection fails
        return cls._client

    @classmethod
    def ping(cls) -> bool:
        """Health check — returns True if Redis is reachable."""
        client = cls.get_client()
        if client:
            try:
                return client.ping()
            except Exception:
                return False
        return False
