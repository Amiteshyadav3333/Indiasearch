import os
import aiohttp
import logging

logger = logging.getLogger(__name__)

async def fetch_news(query: str) -> list:
    """
    Fetches real-time news articles from NewsData.io using explicit API key.
    """
    api_key = os.getenv("apikey") # using the exact name from .env
    if not api_key:
        logger.warning("[NewsService] No 'apikey' found in environment for NewsData.")
        return []

    # Prepare URL
    # We clean the query as NewsData.io works best with basic keywords
    q = query.replace("news", "").strip() or "india" 
    
    url = f"https://newsdata.io/api/1/news?apikey={api_key}&q={q}&country=in&language=en,hi"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                data = await resp.json()
                if data.get("status") == "success":
                    results = []
                    for article in data.get("results", []):
                        results.append({
                            "title": article.get("title", ""),
                            "url": article.get("link", ""),
                            "snippet": article.get("description", "") or article.get("content", "")[:200],
                            "image": article.get("image_url", ""),
                            "source": "news_api",
                            "is_news": True
                        })
                    return results
                else:
                    logger.warning(f"[NewsService] API Error: {data}")
    except Exception as e:
        logger.error(f"[NewsService] Fetch error: {e}")
    return []
