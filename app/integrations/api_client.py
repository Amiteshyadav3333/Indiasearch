# app/integrations/api_client.py
# 💰 Paid API Fallback Client — Last Resort Search
# ─────────────────────────────────────────────────
# Uses SerpAPI (Google Search) as the paid fallback.
# Hard-limited to 100 calls/day via APIQuotaManager.
# Only called when all free sources fail.
#
# Env vars: SERPAPI_KEY, API_DAILY_LIMIT (default 100)

import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor

from app.services.api_quota_manager import APIQuotaManager

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=2)


def _serpapi_sync_search(query: str, max_results: int = 10) -> list:
    """Blocking SerpAPI call — only runs if quota allows."""
    # ── Quota gate ──────────────────────────────────────────
    if not APIQuotaManager.can_call():
        status = APIQuotaManager.status()
        logger.warning(
            f"[API] Daily quota exhausted ({status['used']}/{status['limit']}). "
            f"Skipping paid API call for: {query!r}"
        )
        return []

    api_key = os.getenv("SERPAPI_KEY", "").strip()
    if not api_key:
        logger.warning("[API] SERPAPI_KEY not set — paid fallback skipped.")
        return []

    try:
        import requests
        url = "https://serpapi.com/search"
        params = {
            "q":       query,
            "api_key": api_key,
            "engine":  "google",
            "gl":      "in",
            "hl":      "en",
            "num":     max_results,
        }
        resp = requests.get(url, params=params, timeout=8)
        data = resp.json()

        # ── Increment quota ONLY on successful call ──────────
        count = APIQuotaManager.increment()
        status = APIQuotaManager.status()
        logger.info(
            f"[API] SerpAPI call #{count}/{status['limit']} | "
            f"{status['remaining']} remaining today | query={query!r}"
        )

        results = []
        for r in data.get("organic_results", []):
            results.append({
                "title":   r.get("title", ""),
                "url":     r.get("link", ""),
                "snippet": r.get("snippet", ""),
                "source":  "serpapi",
            })
        return results

    except Exception as e:
        logger.error(f"[API] SerpAPI call failed: {e}")
        return []


async def search(query: str, max_results: int = 10) -> list:
    """Async paid API fallback — respects 100/day quota limit."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor, _serpapi_sync_search, query, max_results
    )


def get_quota_status() -> dict:
    """Return current daily quota status."""
    return APIQuotaManager.status()
