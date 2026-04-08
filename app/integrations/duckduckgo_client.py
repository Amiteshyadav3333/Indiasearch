# app/integrations/duckduckgo_client.py
# 🔍 DuckDuckGo Client — Async-compatible wrapper
# ─────────────────────────────────────────────────
# Uses duckduckgo-search library for free web search.
# Returns normalized list of results.

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

try:
    from duckduckgo_search import DDGS
except ImportError:
    try:
        from ddgs import DDGS
    except ImportError:
        DDGS = None

_executor = ThreadPoolExecutor(max_workers=4)


def _ddg_sync_search(query: str, max_results: int = 10, region: str = "in-en") -> list:
    """Blocking DDG search (runs in thread pool)."""
    if DDGS is None:
        logger.warning("DuckDuckGo library not installed.")
        return []
    try:
        with DDGS() as ddgs:
            raw = list(ddgs.text(query, region=region, max_results=max_results))
        results = []
        for r in raw:
            results.append({
                "title":   r.get("title", ""),
                "url":     r.get("href", ""),
                "snippet": r.get("body", ""),
                "source":  "duckduckgo",
            })
        logger.info(f"[DDG] Got {len(results)} results for: {query!r}")
        return results
    except Exception as e:
        logger.error(f"[DDG] Search failed: {e}")
        return []


async def search(query: str, max_results: int = 10, region: str = "in-en") -> list:
    """Async DDG search — offloads blocking call to thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor, _ddg_sync_search, query, max_results, region
    )

def _ddg_sync_images(query: str, max_results: int = 20, region: str = "in-en") -> list:
    if DDGS is None: return []
    try:
        with DDGS() as ddgs:
            raw = list(ddgs.images(query, region=region, max_results=max_results))
        results = []
        for r in raw:
            results.append({
                "title":   r.get("title", ""),
                "url":     r.get("image", ""),
                "snippet": r.get("source", ""),
                "source":  "duckduckgo_images",
            })
        return results
    except Exception as e:
        logger.error(f"[DDG] Image search failed: {e}")
        return []

async def search_images(query: str, max_results: int = 20, region: str = "in-en") -> list:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor, _ddg_sync_images, query, max_results, region
    )
