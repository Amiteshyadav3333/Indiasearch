# app/cache/hot_query_store.py
# 🔥 Hot Query Store — Cache Warming for Top Queries
# ────────────────────────────────────────────────────
# Tracks query frequency and warms cache for top N popular queries.
# "70-90% queries should be served from cache" — this makes it happen.

import logging
import asyncio
from collections import Counter
from app.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)

# In-memory hit counter (resets on restart, good enough for warming)
_query_counter: Counter = Counter()
_TOP_N = 100  # Track top 100 queries

def record_query(normalized_key: str):
    """Increment the hit count for this query. Called on every search."""
    _query_counter[normalized_key] += 1

def get_top_queries(n: int = _TOP_N) -> list:
    """Return the N most frequent queries."""
    return [q for q, _ in _query_counter.most_common(n)]

def is_hot(normalized_key: str, threshold: int = 3) -> bool:
    """Returns True if this query has been searched >= threshold times."""
    return _query_counter[normalized_key] >= threshold

async def warm_hot_cache(search_fn, top_n: int = 20):
    """
    Background task: Re-run top N queries to warm the cache.
    Call this periodically (e.g. every 30 min) to keep hot results fresh.
    """
    top = get_top_queries(top_n)
    logger.info(f"[HotCache] Warming {len(top)} hot queries...")
    for q in top:
        try:
            # Only warm if NOT already in cache
            cache_key = CacheManager.make_key("brain:search:v5", "en", q, 1, "general", "all")
            if not CacheManager.get(cache_key):
                await search_fn(q, page=1, filter="all")
                logger.info(f"[HotCache] Warmed: {q!r}")
            await asyncio.sleep(0.5)  # Throttle
        except Exception as e:
            logger.warning(f"[HotCache] Failed to warm {q!r}: {e}")
    logger.info("[HotCache] Cache warming complete.")
