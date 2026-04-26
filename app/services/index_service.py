# app/services/index_service.py
import logging
from app.integrations.elastic_client import ElasticClient
import re

logger = logging.getLogger(__name__)

import aiohttp
from bs4 import BeautifulSoup
import asyncio

# ---------- CLEAN TEXT ----------
def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ---------- ADVANCED SPAM DETECTOR ----------
def is_spam(url, content):
    spam_words = [
        "casino", "betting", "loan fast", "xxx", "porn", "viagra", 
        "sex", "escort", "slot", "satta", "matka", "gambling",
        "free robux", "hack generator", "buy cheap", "adult dating"
    ]
    text = (str(url) + " " + str(content)).lower()
    return any(w in text for w in spam_words)

# ---------- DEEP CRAWLER HELPER ----------
async def fetch_page_text(url: str, default_text: str) -> str:
    """Asynchronously fetches the full page content for deeper indexing."""
    try:
        async with aiohttp.ClientSession() as session:
            # Short timeout so it doesn't hang
            async with session.get(url, timeout=3) as resp:
                if resp.status == 200 and "text/html" in resp.headers.get("Content-Type", ""):
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")
                    text = " ".join([p.get_text() for p in soup.find_all("p")])
                    if text.strip():
                        # Return snippet combined with full text, up to 10k chars
                        return (default_text + " " + text)[:10000]
    except Exception:
        pass
    return default_text

# ---------- MAIN INDEX FUNCTION ----------
async def index_results_async(results: list):
    """
    Background worker to index fresh results found from web search.
    Follows 'Fresh Indexing' requirement.
    """
    if not results:
        return

    indexed_count = 0
    # Process only top 5 to keep background load light
    for r in results[:5]:
        url = r.get("url")
        title = r.get("title")
        snippet = r.get("snippet", "")
        
        if not url or not title:
            continue
            
        if is_spam(url, snippet):
            continue
            
        # Deep Indexing: Fetch the full page content instead of just the snippet
        full_content = await fetch_page_text(url, snippet)
        
        # Double check spam on full content
        if is_spam(url, full_content):
            continue

        doc = {
            "title": clean_text(title),
            "url": url,
            "content": clean_text(full_content),
            "indexed_at": "now",
            "source": r.get("source", "web_discovery")
        }
        
        # Use ElasticClient to index asynchronously
        import hashlib
        doc_id = hashlib.md5(url.encode()).hexdigest()
        
        success = await ElasticClient.index_async(doc, doc_id=doc_id)
        if success:
            indexed_count += 1
            
    if indexed_count > 0:
        logger.info(f"[IndexService] Freshly indexed {indexed_count} new results for future searches.")

def index_document_sync(url, title, content):
    """Synchronous version for one-off indexing."""
    title = clean_text(title)
    content = clean_text(content)
    
    if is_spam(url, content):
        return

    doc = {
        "title": title,
        "url": url,
        "content": content
    }
    ElasticClient.index_doc(doc)
