# app/integrations/wiki_client.py
import aiohttp
import logging
import urllib.parse

logger = logging.getLogger(__name__)

async def search(query: str, max_results: int = 5) -> list:
    """
    Search Wikipedia for the query and return a list of matching pages.
    Very reliable fallback.
    """
    search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json"
    headers = {"User-Agent": "Indiasearch/1.0 (https://indiasearch.com; amitesh@example.com)"}
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(search_url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    search_results = data.get("query", {}).get("search", [])
                    
                    results = []
                    for item in search_results[:max_results]:
                        title = item.get("title")
                        snippet = item.get("snippet", "").replace('<span class="searchmatch">', '').replace('</span>', '')
                        page_url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                        
                        results.append({
                            "title": title + " - Wikipedia",
                            "url": page_url,
                            "snippet": snippet + "...",
                            "source": "wikipedia"
                        })
                    
                    logger.info(f"[Wiki] Found {len(results)} results")
                    return results
    except Exception as e:
        logger.error(f"[Wiki] Error: {e}")
        
    return []
