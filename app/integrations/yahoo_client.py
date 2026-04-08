# app/integrations/yahoo_client.py
# 📊 Yahoo Search Client — Async-compatible wrapper
# ─────────────────────────────────────────────────
# Uses requests + BeautifulSoup to scrape Yahoo Search.
# Also supports Yahoo Finance for stock queries.
# Returns normalized list of results.

import asyncio
import logging
import re
import time
import random
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=4)

_HEADERS_POOL = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Accept-Language": "en-IN,en;q=0.9",
    },
]


def _yahoo_sync_search(query: str, max_results: int = 10) -> list:
    """Blocking Yahoo search via requests + BeautifulSoup."""
    try:
        import requests
        from bs4 import BeautifulSoup

        url = f"https://search.yahoo.com/search?p={query}&n={max_results}"
        headers = random.choice(_HEADERS_POOL)
        resp = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []
        for tag in soup.select("div.algo"):
            a = tag.select_one("h3 a") or tag.select_one("a.ac-algo")
            desc = tag.select_one("p.fz-ms") or tag.select_one(".compText p")
            if not a:
                continue
            raw_url = a.get("href", "")
            # Yahoo wraps URLs in redirects — extract real URL
            m = re.search(r"https?://[^&]+", raw_url)
            clean_url = m.group(0) if m else raw_url

            results.append({
                "title":   a.get_text(strip=True),
                "url":     clean_url,
                "snippet": desc.get_text(strip=True) if desc else "",
                "source":  "yahoo",
            })
            if len(results) >= max_results:
                break

        logger.info(f"[Yahoo] Got {len(results)} results for: {query!r}")
        return results
    except Exception as e:
        logger.error(f"[Yahoo] Search failed: {e}")
        return []


async def search(query: str, max_results: int = 10) -> list:
    """Async Yahoo search — offloads blocking call to thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor, _yahoo_sync_search, query, max_results
    )

def _yahoo_sync_images(query: str, max_results: int = 20) -> list:
    """Blocking Yahoo Image search via requests + BeautifulSoup."""
    try:
        import requests
        from bs4 import BeautifulSoup

        url = f"https://images.search.yahoo.com/search/images?p={query}"
        headers = random.choice(_HEADERS_POOL)
        resp = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []
        for tag in soup.select("li.ld a"):
            img = tag.select_one("img")
            if not img:
                continue
            
            src = img.get("data-src") or img.get("src")
            if not src or src.startswith("data:"):
                continue
                
            results.append({
                "title": img.get("alt", "") or tag.get("aria-label", "Image"),
                "url": src,
                "snippet": "Yahoo Images",
                "source": "yahoo_images"
            })
            if len(results) >= max_results:
                break
                
        logger.info(f"[Yahoo Images] Got {len(results)} results for: {query!r}")
        return results
    except Exception as e:
        logger.error(f"[Yahoo Images] Image Search failed: {e}")
        return []

async def search_images(query: str, max_results: int = 20) -> list:
    """Async Yahoo Image search."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor, _yahoo_sync_images, query, max_results
    )
