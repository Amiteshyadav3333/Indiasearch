# app/middleware/rate_limiter.py
# 🛡️ Rate Limiter — Per-IP & Per-User Throttling
# ----------------------------------------
# Uses Flask-Limiter backed by Redis to enforce request limits.
# This prevents abuse, scraping, and DDoS at the application layer.
#
# Default limits (configurable via .env):
#   Global:       200 requests/day, 50/hour  per IP
#   Search API:   30 requests/minute          per IP
#   Auth API:     5  requests/minute          per IP (brute force protection)
#
# Usage:
#   @search_bp.get("/web")
#   @limiter.limit("30/minute")
#   def web_search(): ...
#
# Required packages: flask-limiter, redis (backend)

# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
# from app.cache.redis_client import RedisClient
# from app.config.settings import Settings


# limiter = Limiter(
#     key_func=get_remote_address,
#     default_limits=["200 per day", "50 per hour"],
#     storage_uri=Settings.REDIS_URL,
# )


class RateLimiter:
    """
    Placeholder class.
    TODO: Replace with flask-limiter integration above.
    """
    pass
