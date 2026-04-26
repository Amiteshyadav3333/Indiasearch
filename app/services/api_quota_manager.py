# app/services/api_quota_manager.py
# 💰 API Quota Manager — Daily Rate Limiter
# ─────────────────────────────────────────
# Enforces hard daily limits for paid fallback API calls.
# Uses Redis if available, falls back to in-memory counter.
# Resets automatically at midnight (IST / UTC+5:30).
#
# Usage:
#   from app.services.api_quota_manager import APIQuotaManager
#   if APIQuotaManager.can_call():
#       APIQuotaManager.increment()
#       # ... make API call ...
#   else:
#       # skip / return fallback

import os
import time
import logging
from datetime import datetime, timezone, timedelta
from app.cache.redis_client import RedisClient

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────
DAILY_API_LIMIT = int(os.getenv("API_DAILY_LIMIT", "100"))
PROVIDER_LIMITS = {
    "default": DAILY_API_LIMIT,
    "bing": int(os.getenv("BING_DAILY_LIMIT", str(DAILY_API_LIMIT))),
    "serper": int(os.getenv("SERPER_DAILY_LIMIT", "80")),
}
IST = timezone(timedelta(hours=5, minutes=30))

# ── In-memory fallback ────────────────────────────────────
_mem_counts: dict[str, int] = {}
_mem_date: str = ""          # "YYYY-MM-DD" in IST


def _today_ist() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d")


def _get_redis():
    """Shared Redis client for quota."""
    return RedisClient.get_client()


class APIQuotaManager:
    """
    Tracks and enforces the daily API call limit (default: 100/day).
    
    Methods:
        can_call()   → bool  : True if quota not exhausted
        increment()  → int   : Increment counter, return new count
        remaining()  → int   : Calls remaining today
        status()     → dict  : Full status dict
    """

    @staticmethod
    def _normalize_provider(provider: str = "default") -> str:
        return (provider or "default").strip().lower()

    @staticmethod
    def _limit(provider: str = "default") -> int:
        return PROVIDER_LIMITS.get(APIQuotaManager._normalize_provider(provider), DAILY_API_LIMIT)

    @staticmethod
    def _redis_key(provider: str = "default") -> str:
        provider = APIQuotaManager._normalize_provider(provider)
        return f"api_quota:{provider}:{_today_ist()}"

    @staticmethod
    def can_call(provider: str = "default") -> bool:
        """Return True if we still have quota remaining today."""
        return APIQuotaManager.remaining(provider) > 0

    @staticmethod
    def remaining(provider: str = "default") -> int:
        """Return number of API calls still allowed today."""
        used = APIQuotaManager._get_count(provider)
        return max(0, APIQuotaManager._limit(provider) - used)

    @staticmethod
    def increment(provider: str = "default") -> int:
        """Increment today's counter. Returns new count."""
        global _mem_counts, _mem_date

        provider = APIQuotaManager._normalize_provider(provider)

        r = _get_redis()
        if r:
            try:
                key = APIQuotaManager._redis_key(provider)
                count = r.incr(key)
                # Set TTL = seconds until midnight IST
                now_ist = datetime.now(IST)
                midnight = (now_ist + timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                ttl = int((midnight - now_ist).total_seconds())
                r.expire(key, ttl)
                logger.info(f"[Quota:{provider}] API call #{count}/{APIQuotaManager._limit(provider)} today.")
                return int(count)
            except Exception as e:
                logger.warning(f"[Quota] Redis increment failed: {e}")

        # In-memory fallback
        today = _today_ist()
        if _mem_date != today:
            _mem_counts = {}
            _mem_date = today
        _mem_counts[provider] = _mem_counts.get(provider, 0) + 1
        logger.info(f"[Quota:{provider}] API call #{_mem_counts[provider]}/{APIQuotaManager._limit(provider)} today (memory).")
        return _mem_counts[provider]

    @staticmethod
    def _get_count(provider: str = "default") -> int:
        """Get current count for today."""
        global _mem_counts, _mem_date

        provider = APIQuotaManager._normalize_provider(provider)

        r = _get_redis()
        if r:
            try:
                val = r.get(APIQuotaManager._redis_key(provider))
                return int(val) if val else 0
            except Exception:
                pass

        today = _today_ist()
        if _mem_date != today:
            _mem_counts = {}
            _mem_date = today
        return _mem_counts.get(provider, 0)

    @staticmethod
    def status(provider: str = "default") -> dict:
        """Return full quota status as a dict."""
        provider = APIQuotaManager._normalize_provider(provider)
        limit = APIQuotaManager._limit(provider)
        used = APIQuotaManager._get_count(provider)
        remaining = max(0, limit - used)
        return {
            "provider":      provider,
            "date_ist":      _today_ist(),
            "limit":         limit,
            "used":          used,
            "remaining":     remaining,
            "exhausted":     remaining == 0,
            "backend":       "redis" if _get_redis() else "memory",
        }

    @staticmethod
    def status_all() -> dict:
        """Return quota status for all paid fallback providers."""
        return {
            "bing": APIQuotaManager.status("bing"),
            "serper": APIQuotaManager.status("serper"),
        }
