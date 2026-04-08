# app/services/api_quota_manager.py
# 💰 API Quota Manager — Daily Rate Limiter
# ─────────────────────────────────────────
# Enforces a hard daily limit of 100 API calls.
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
IST = timezone(timedelta(hours=5, minutes=30))

# ── In-memory fallback ────────────────────────────────────
_mem_count: int = 0
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
    def _redis_key() -> str:
        return f"api_quota:{_today_ist()}"

    @staticmethod
    def can_call() -> bool:
        """Return True if we still have quota remaining today."""
        return APIQuotaManager.remaining() > 0

    @staticmethod
    def remaining() -> int:
        """Return number of API calls still allowed today."""
        used = APIQuotaManager._get_count()
        return max(0, DAILY_API_LIMIT - used)

    @staticmethod
    def increment() -> int:
        """Increment today's counter. Returns new count."""
        global _mem_count, _mem_date

        r = _get_redis()
        if r:
            try:
                key = APIQuotaManager._redis_key()
                count = r.incr(key)
                # Set TTL = seconds until midnight IST
                now_ist = datetime.now(IST)
                midnight = (now_ist + timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                ttl = int((midnight - now_ist).total_seconds())
                r.expire(key, ttl)
                logger.info(f"[Quota] API call #{count}/{DAILY_API_LIMIT} today.")
                return int(count)
            except Exception as e:
                logger.warning(f"[Quota] Redis increment failed: {e}")

        # In-memory fallback
        today = _today_ist()
        if _mem_date != today:
            _mem_count = 0
            _mem_date = today
        _mem_count += 1
        logger.info(f"[Quota] API call #{_mem_count}/{DAILY_API_LIMIT} today (memory).")
        return _mem_count

    @staticmethod
    def _get_count() -> int:
        """Get current count for today."""
        global _mem_count, _mem_date

        r = _get_redis()
        if r:
            try:
                val = r.get(APIQuotaManager._redis_key())
                return int(val) if val else 0
            except Exception:
                pass

        today = _today_ist()
        if _mem_date != today:
            _mem_count = 0
            _mem_date = today
        return _mem_count

    @staticmethod
    def status() -> dict:
        """Return full quota status as a dict."""
        used = APIQuotaManager._get_count()
        remaining = max(0, DAILY_API_LIMIT - used)
        return {
            "date_ist":      _today_ist(),
            "limit":         DAILY_API_LIMIT,
            "used":          used,
            "remaining":     remaining,
            "exhausted":     remaining == 0,
            "backend":       "redis" if _get_redis() else "memory",
        }
