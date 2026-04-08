# app/services/index_service.py
import logging
from app.integrations.elastic_client import ElasticClient
import re

logger = logging.getLogger(__name__)

# ---------- CLEAN TEXT ----------
def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ---------- SIMPLE SPAM DETECTOR ----------
def is_spam(url, content):
    spam_words = [
        "casino", "betting", "loan fast", "xxx",
        "earn money fast", "porn", "viagra"
    ]
    text = (str(url) + " " + str(content)).lower()
    return any(w in text for w in spam_words)

# ---------- MAIN INDEX FUNCTION ----------
async def index_results_async(results: list):
    """
    Background worker to index fresh results found from web search.
    Follows 'Fresh Indexing' requirement.
    """
    if not results:
        return

    indexed_count = 0
    for r in results:
        url = r.get("url")
        title = r.get("title")
        snippet = r.get("snippet")
        
        if not url or not title:
            continue
            
        if is_spam(url, snippet):
            continue
            
        doc = {
            "title": clean_text(title),
            "url": url,
            "content": clean_text(snippet),
            "indexed_at": "now",
            "source": r.get("source", "web_discovery")
        }
        
        # Use ElasticClient to index asynchronously
        # Using a simple doc_id based on URL to avoid duplicates in ES
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
