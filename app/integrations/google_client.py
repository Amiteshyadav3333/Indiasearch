# app/integrations/google_client.py
import asyncio
import logging
import random
import re
import aiohttp
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=5)

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

async def search(query: str, max_results: int = 10) -> list:
    """Async Google Search scraper."""
    url = f"https://www.google.com/search?q={query}"
    headers = {"User-Agent": random.choice(_USER_AGENTS)}
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=5) as resp:
                if resp.status != 200:
                    logger.warning(f"[Google] Failed with status {resp.status}")
                    return []
                
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")
                
                results = []
                # Google changed layout frequently, using a more robust selector
                for g in soup.select(".g"):
                    anchor = g.select_one("a")
                    title_tag = g.select_one("h3")
                    snippet_tag = g.select_one(".VwiC3b") or g.select_one(".IsZ68c") or g.select_one(".yXK7u")
                    
                    if anchor and title_tag:
                        url_str = anchor["href"]
                        if url_str.startswith("/url?q="):
                            url_str = url_str.split("/url?q=")[1].split("&")[0]
                        
                        results.append({
                            "title": title_tag.get_text(strip=True),
                            "url": url_str,
                            "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "",
                            "source": "google"
                        })
                    if len(results) >= max_results:
                        break
                
                logger.info(f"[Google] Found {len(results)} results")
                return results
    except Exception as e:
        logger.error(f"[Google] Error: {e}")
        return []
