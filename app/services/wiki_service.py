import aiohttp
import asyncio
import logging

logger = logging.getLogger(__name__)

async def fetch_knowledge_panel(query: str) -> dict:
    """
    Fetches a brief summary and main image from Wikipedia for famous entities 
    (like Narendra Modi, Virat Kohli) to populate the Knowledge Panel.
    """
    # Clean the query for wiki search
    q = query.title().replace(" ", "_").strip()
    
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{q}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=3) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # Discard if it's a disambiguation page
                    if data.get("type") == "disambiguation" or "may refer to:" in data.get("extract", ""):
                        return None
                        
                    image_url = data.get("thumbnail", {}).get("source")
                    # If high res original image exists, try to get it
                    if data.get("originalimage", {}).get("source"):
                        image_url = data.get("originalimage", {}).get("source")

                    return {
                        "title": data.get("title", ""),
                        "snippet": data.get("extract", ""),
                        "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                        "image": image_url
                    }
    except Exception as e:
        logger.error(f"[WikiService] Error fetching info: {e}")
        
    return None
