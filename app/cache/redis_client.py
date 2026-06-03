# app/cache/redis_client.py
# ⚡ Redis Connection — Singleton Client
# ----------------------------------------
# Provides a single shared Redis connection pool.
#
# Required env: REDIS_URL (e.g. redis://localhost:6379/0)
#               Set in .env → loaded by app/config/settings.py

import os
import logging
import time
from typing import Any, Optional

try:
    import redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)

class RedisClient:
    """Singleton Redis connection pool wrapper."""

    _client: Optional[Any] = None
    _last_attempt_time: float = 0.0
    _retry_delay: float = 30.0  # Avoid reconnecting on every request if down

    @classmethod
    def get_client(cls) -> Optional[Any]:
        """
        Return the shared Redis client (lazy singleton).
        Uses connection pooling for production safety.
        """
        if redis is None:
            return None

        if cls._client is None:
            now = time.time()
            if now - cls._last_attempt_time < cls._retry_delay:
                return None
            cls._last_attempt_time = now

            url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            try:
                # Upstash and other cloud Redis providers use rediss:// (SSL)
                kwargs = dict(
                    decode_responses=True,
                    max_connections=20,
                    socket_connect_timeout=3,
                    socket_timeout=3,
                )
                # Add SSL cert bypass for Upstash (uses self-signed certs)
                if url.startswith("rediss://"):
                    kwargs["ssl_cert_reqs"] = None

                cls._client = redis.from_url(url, **kwargs)
                cls._client.ping()  # Early health check
                logger.info(f"[Redis] ✅ Connected to: {url.split('@')[-1]}")  # Hide password in logs
            except Exception as e:
                if "localhost" not in url:
                    logger.error(f"[Redis] ❌ Connection failed: {e}")
                cls._client = None
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
