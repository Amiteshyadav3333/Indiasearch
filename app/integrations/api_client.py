# app/integrations/api_client.py
# 💎 Paid Search API Fallbacks
# ─────────────────────────────────────────────────
# Uses free/local providers first in search_manager.
# This module is called only when those results are weak.
# Fallback order: Bing first, then Serper as the last paid resort.

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
    if not APIQuotaManager.can_call("bing"):
        quota = APIQuotaManager.status("bing")
        logger.warning(f"[Bing] Quota exhausted ({quota['used']}/{quota['limit']}). Skipping call for: {query!r}")
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
        count = APIQuotaManager.increment("bing")
        limit = APIQuotaManager.status("bing")["limit"]
        logger.info(f"[Bing] API call #{count}/{limit} | query={query!r}")

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

def _get_serper_api_key() -> str:
    """Read the Serper key while tolerating the mixed-case name in existing .env files."""
    for key in ("SERPER_API_KEY", "serper_API_KEY", "serper_API_KEy", "Serper_API_KEY"):
        value = os.getenv(key, "").strip()
        if value:
            return value
    return ""

def _serper_sync_search(query: str, max_results: int = 10) -> list:
    """
    Blocking Serper API call.
    Last-resort paid fallback, hard-limited separately to 80/day by default.
    """
    if not APIQuotaManager.can_call("serper"):
        quota = APIQuotaManager.status("serper")
        logger.warning(f"[Serper] Quota exhausted ({quota['used']}/{quota['limit']}). Skipping call for: {query!r}")
        return []

    api_key = _get_serper_api_key()
    if not api_key:
        logger.warning("[Serper] SERPER_API_KEY / serper_API_KEY not set in .env")
        return []

    endpoint = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "q": query,
        "num": max_results,
        "gl": "in",
        "hl": "en",
    }

    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        count = APIQuotaManager.increment("serper")
        limit = APIQuotaManager.status("serper")["limit"]
        logger.info(f"[Serper] API call #{count}/{limit} | query={query!r}")

        results = []
        for item in data.get("organic", [])[:max_results]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "source": "serper_api",
            })

        answer_box = data.get("answerBox") or {}
        if answer_box.get("link") and answer_box.get("title"):
            results.insert(0, {
                "title": answer_box.get("title", ""),
                "url": answer_box.get("link", ""),
                "snippet": answer_box.get("answer") or answer_box.get("snippet") or "",
                "source": "serper_answer_box",
                "_boost": 3,
            })

        knowledge_graph = data.get("knowledgeGraph") or {}
        if knowledge_graph.get("website") and knowledge_graph.get("title"):
            results.insert(0, {
                "title": knowledge_graph.get("title", ""),
                "url": knowledge_graph.get("website", ""),
                "snippet": knowledge_graph.get("description", ""),
                "source": "serper_knowledge_graph",
                "_boost": 2,
            })

        return results[:max_results]

    except Exception as e:
        logger.error(f"[Serper] API call error: {e}")
        return []

async def search(query: str, max_results: int = 10) -> list:
    """
    Async paid fallback wrapper.
    Bing gets the first chance. Serper is called only if Bing gives no usable results.
    """
    loop = asyncio.get_event_loop()
    bing_results = await loop.run_in_executor(
        _executor, _bing_sync_search, query, max_results
    )
    if bing_results:
        return bing_results

    logger.info(f"[PaidFallback] Bing returned no results. Trying Serper as last resort for: {query!r}")
    return await loop.run_in_executor(
        _executor, _serper_sync_search, query, max_results
    )

def _serper_sync_images(query: str, max_results: int = 20) -> list:
    if not APIQuotaManager.can_call("serper"):
        quota = APIQuotaManager.status("serper")
        logger.warning(f"[Serper Images] Quota exhausted ({quota['used']}/{quota['limit']}). Skipping call for: {query!r}")
        return []

    api_key = _get_serper_api_key()
    if not api_key: return []
    try:
        resp = requests.post(
            "https://google.serper.dev/images", 
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": max_results, "gl": "in"},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()

        count = APIQuotaManager.increment("serper")
        limit = APIQuotaManager.status("serper")["limit"]
        logger.info(f"[Serper Images] API call #{count}/{limit} | query={query!r}")

        results = []
        for item in data.get("images", [])[:max_results]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("imageUrl", ""),
                "snippet": item.get("source", ""),
                "source": "serper_images"
            })
        return results
    except Exception as e:
        logger.error(f"[Serper Images] Error: {e}")
        return []

async def search_images(query: str, max_results: int = 20) -> list:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _serper_sync_images, query, max_results)

def _serper_sync_videos(query: str, max_results: int = 20) -> list:
    if not APIQuotaManager.can_call("serper"):
        quota = APIQuotaManager.status("serper")
        logger.warning(f"[Serper Videos] Quota exhausted ({quota['used']}/{quota['limit']}). Skipping call for: {query!r}")
        return []

    api_key = _get_serper_api_key()
    if not api_key: return []
    try:
        resp = requests.post(
            "https://google.serper.dev/videos", 
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": max_results, "gl": "in"},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()

        count = APIQuotaManager.increment("serper")
        limit = APIQuotaManager.status("serper")["limit"]
        logger.info(f"[Serper Videos] API call #{count}/{limit} | query={query!r}")

        results = []
        for item in data.get("videos", [])[:max_results]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "image": item.get("imageUrl", ""),
                "snippet": item.get("snippet", ""),
                "source": "serper_videos"
            })
        return results
    except Exception as e:
        logger.error(f"[Serper Videos] Error: {e}")
        return []

async def search_videos(query: str, max_results: int = 20) -> list:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _serper_sync_videos, query, max_results)

def get_quota_status() -> dict:
    return APIQuotaManager.status_all()
