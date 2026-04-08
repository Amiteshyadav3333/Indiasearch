# app/integrations/api_client.py
# 💎 Paid Bing Search API Fallback
# ─────────────────────────────────────────────────
# Uses Microsoft Bing Search API as the premium fallback.
# Hard-limited to 100 calls/day via APIQuotaManager.

import asyncio
import logging
import os
import requests
from concurrent.futures import ThreadPoolExecutor
from app.services.api_quota_manager import APIQuotaManager

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=2)

def _bing_sync_search(query: str, max_results: int = 10) -> list:
    """Blocking Bing API call."""
    # ── Quota gate ──────────────────────────────────────────
    if not APIQuotaManager.can_call():
        logger.warning(f"[Bing] Quota exhausted (100/100). Skipping call for: {query!r}")
        return []

    api_key = os.getenv("BING_API_KEY", "").strip()
    if not api_key:
        logger.warning("[Bing] BING_API_KEY not set in .env")
        return []

    endpoint = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": api_key}
    params = {
        "q": query,
        "count": max_results,
        "mkt": "en-IN",  # India specific market
        "safeSearch": "Moderate"
    }

    try:
        resp = requests.get(endpoint, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # ── Increment quota ──────────
        count = APIQuotaManager.increment()
        logger.info(f"[Bing] API call #{count}/100 | query={query!r}")

        results = []
        pages = data.get("webPages", {}).get("value", [])
        for p in pages:
            results.append({
                "title":   p.get("name", ""),
                "url":     p.get("url", ""),
                "snippet": p.get("snippet", ""),
                "source":  "bing_api",
            })
        return results

    except Exception as e:
        logger.error(f"[Bing] API call error: {e}")
        return []

async def search(query: str, max_results: int = 10) -> list:
    """Async Bing search wrapper."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor, _bing_sync_search, query, max_results
    )

def get_quota_status() -> dict:
    return APIQuotaManager.status()
