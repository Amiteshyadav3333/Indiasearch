# app/services/search_manager.py
# 🧠 INTELLIGENT SEARCH BRAIN — Orchestrator & Multi-Level Pipeline
# ──────────────────────────────────────────────────────────────
# 1. Intent Detection (News, Weather, Sports, Finance, AI)
# 2. Level 0: Redis Cache Hit
# 3. Level 1: Parallel (Local Index + DDG + Yahoo)
# 4. Level 2: Deduplication & Fresh Indexing
# 5. Level 3: Fallback (Bing API - 100/day hard limit)
# ──────────────────────────────────────────────────────────────

import asyncio
import logging
import time
import re
from datetime import datetime

from app.cache.cache_manager import CacheManager, SEARCH_TTL
from app.integrations import duckduckgo_client, yahoo_client, api_client, google_client, wiki_client
from app.integrations.elastic_client import ElasticClient
from app.services import (
    merge_service, 
    ranking_service, 
    index_service,
    weather_service,
    cricket_service,
    finance_service,
    ai_service,
    news_service,
    wiki_service
)
from app.services.api_quota_manager import APIQuotaManager
from app.utils import translator

logger = logging.getLogger(__name__)

# ── Tunables ──────────────────────────────────────────────
PARALLEL_TIMEOUT    = 3.0    # total timeout for free sources
MIN_QUALITY_RESULTS = 5      # fallback to Bing if below this
MAX_WEB_RESULTS     = 10
# ──────────────────────────────────────────────────────────

async def identify_intent(query: str) -> str:
    """
    The 'Brain' element: Understands what the user is asking.
    Categories: news, weather, sports, finance, ai, general
    """
    q = query.lower().strip()
    
    # AI Mode Intent
    if any(k in q for k in ["ask ai", "ai mode", "askai", "tell me about"]):
        return "ai"
    
    # News Intent
    if any(k in q for k in ["news", "latest", "breaking", "update", "samachar", "khabar"]):
        return "news"
    
    # Weather Intent
    if any(k in q for k in ["weather", "temperature", "temp", "forecast", "mausam", "rain"]):
        return "weather"
    
    # Sports Intent (Cricket focus for IndiaSearch)
    if any(k in q for k in ["score", "cricket", "ipl", "match", "t20", "world cup", "sports"]):
        return "sports"
    
    # Finance Intent
    if any(k in q for k in ["stock", "price", "share", "nifty", "sensex", "market", "nasdaq", "crypto"]):
        return "finance"
    
    return "general"

def get_direct_hit(query: str) -> list:
    """
    Returns a 'Direct Hit' result if the query looks like a domain or major brand.
    """
    q = query.lower().strip()
    
    # Common TLDs to detect domains (more robust regex)
    if re.search(r"\.[a-z]{2,12}$", q) or q.startswith("www."):
        clean_domain = q.replace("www.", "")
        name = clean_domain.split(".")[0].capitalize()
        url = q if q.startswith("http") else f"https://{q}"
        return [{
            "title": f"{name} - Official Site",
            "url": url,
            "snippet": f"Visit {clean_domain} directly. This matches your exact domain search.",
            "source": "direct_hit",
            "_boost": 10
        }]
    
    # Major Brands
    brands = {
        "google": "https://www.google.com",
        "instagram": "https://www.instagram.com",
        "facebook": "https://www.facebook.com",
        "youtube": "https://www.youtube.com",
        "twitter": "https://www.twitter.com",
        "x": "https://www.twitter.com",
        "linkedin": "https://www.linkedin.com",
        "indiasearch": "https://indiasearch.site",
    }
    
    if q in brands:
        return [{
            "title": f"{q.capitalize()} - Official Website",
            "url": brands[q],
            "snippet": f"Navigate to the official {q.capitalize()} platform.",
            "source": "direct_hit",
            "_boost": 10
        }]
        
    return []

async def run_parallel_pipeline(query: str, page: int = 1, filter: str = "all", lang: str = "en", force_ai: bool = False, pdf_content: str = None) -> dict:
    """
    Master Orchestrator implementing the user's requested architecture.
    """
    start_time = time.time()
    
    # ── Step 0: Translate if needed ────────────────────────
    en_query, detected_lang = translator.translate_query_to_english(query)
    
    # ── Step 1: Identify Intent ────────────────────────────
    intent = await identify_intent(en_query)
    if force_ai: intent = "ai"
    
    logger.info(f"[Brain] Query: {query!r} | Intent: {intent} | Lang: {detected_lang}")

    # ── Step 2: Cache Check ────────────────────────────────
    cache_key = CacheManager.make_key("brain:search", detected_lang, query, page, intent)
    cached = CacheManager.get(cache_key)
    if cached:
        cached["from_cache"] = True
        cached["took_ms"] = round((time.time() - start_time) * 1000, 1)
        return cached

    results = []
    sources_used = []
    special_data = None

    # ── Level 1: Intent-Specific Data Fetch ───────────────
    if intent == "weather":
        special_data = await weather_service.fetch_weather(en_query)
        sources_used.append("weather_api")
    elif intent == "sports":
        special_data = await cricket_service.fetch_live_score()
        sources_used.append("cricket_api")
    elif intent == "finance":
        special_data = await finance_service.fetch_stock(en_query)
        sources_used.append("finance_api")

    # ── Level 2: Parallel Search (Local + Web) ────────────
    tasks = []
    
    if filter == "images":
        # EXCLUSIVE IMAGE SEARCH: DuckDuckGo + Yahoo
        tasks.append(asyncio.create_task(duckduckgo_client.search_images(en_query, max_results=MAX_WEB_RESULTS)))
        tasks.append(asyncio.create_task(yahoo_client.search_images(en_query, max_results=MAX_WEB_RESULTS)))
        # Do not run AI summary or Text indexing for Images
    else:
        # 1. Local Elasticsearch
        tasks.append(asyncio.create_task(ElasticClient.search_async(en_query, max_results=MAX_WEB_RESULTS)))
        
        # 2. DuckDuckGo (Free Web)
        tasks.append(asyncio.create_task(duckduckgo_client.search(en_query, max_results=MAX_WEB_RESULTS)))
        
        # 3. Yahoo (Free Web)
        tasks.append(asyncio.create_task(yahoo_client.search(en_query, max_results=MAX_WEB_RESULTS)))

        # 4. Google (Scraper)
        tasks.append(asyncio.create_task(google_client.search(en_query, max_results=MAX_WEB_RESULTS)))

        # 5. Wikipedia (Reliable)
        tasks.append(asyncio.create_task(wiki_client.search(en_query, max_results=5)))
    
        # 4. News API (If News Intent)
        if intent == "news":
            tasks.append(asyncio.create_task(news_service.fetch_news(en_query)))

    # Fetch Knowledge panel simultaneously for general searches
    kp_task = None
    if filter == "all" and page == 1:
        kp_task = asyncio.create_task(wiki_service.fetch_knowledge_panel(en_query))

    done, pending = await asyncio.wait(tasks, timeout=PARALLEL_TIMEOUT)
    
    search_collections = []
    
    # ── Level 2.5: Direct Hit Detection ───────────────────
    direct_hits = get_direct_hit(en_query)
    if direct_hits:
        search_collections.append(direct_hits)
        sources_used.append("direct_hit")

    for task in done:
        try:
            res = await task
            if res: search_collections.append(res)
        except Exception as e:
            logger.error(f"[Brain] Parallel search error: {e}")

    # Cancel slow tasks
    for task in pending: task.cancel()

    # ── Level 3: Merge & Deduplicate ──────────────────────
    merged_results = merge_service.merge_and_deduplicate(search_collections)
    filtered_results = merge_service.filter_results(merged_results)
    
    # Track sources from merged
    for r in filtered_results:
        src = r.get("source")
        if src and src not in sources_used: sources_used.append(src)

    # ── Level 4: Fallback to Paid API (Bing/SerpAPI) ──────
    quota = APIQuotaManager.status()
    if len(filtered_results) < MIN_QUALITY_RESULTS and intent not in ["weather", "sports", "finance"]:
        if APIQuotaManager.can_call():
            logger.info(f"[Brain] Weak results ({len(filtered_results)}). Triggering fallback API.")
            api_res = await api_client.search(en_query, max_results=MAX_WEB_RESULTS)
            if api_res:
                sources_used.append("fallback_api")
                filtered_results = merge_service.merge_and_deduplicate([filtered_results, api_res])
                quota = APIQuotaManager.status() # Update status
        else:
            logger.warning("[Brain] API Quota exhausted. Staying with free results.")

    # ── Level 5: Rank & Fresh Indexing ────────────────────
    final_ranked = ranking_service.rank(filtered_results, en_query)
    
    # ASYNC TASK: Index fresh results in background for future fast search
    if filtered_results:
        # Don't wait for indexing to finish to respond to user
        asyncio.create_task(index_service.index_results_async(filtered_results))

    # ── Level 6: AI Summary (Google-like AI Overview) ─────
    ai_summary = None
    if page == 1 or force_ai or intent == "ai":
        ai_summary = await asyncio.to_thread(
            ai_service.generate_ai_summary, 
            query=query, 
            docs=final_ranked, 
            ai_mode=True, 
            lang=("Hindi" if detected_lang == "hi" else "English"),
            pdf_content=pdf_content
        )

    # ── Level 7: Retrieve Knowledge Panel ────────
    knowledge_panel = None
    if kp_task:
        try:
            knowledge_panel = await kp_task
        except:
            pass

    # Final pagination
    offset = (page - 1) * MAX_WEB_RESULTS
    paginated = final_ranked[offset : offset + MAX_WEB_RESULTS]

    took_ms = round((time.time() - start_time) * 1000, 1)
    
    response = {
        "results": paginated,
        "intent": intent,
        "special_data": special_data,
        "knowledge_panel": knowledge_panel,
        "ai_summary": ai_summary if filter != "images" else None,
        "total": len(final_ranked),
        "sources_used": sources_used,
        "quota_status": quota,
        "took_ms": took_ms,
        "from_cache": False
    }

    # ── Step 7: Cache final response ──────────────────────
    CacheManager.set(cache_key, response, ttl=SEARCH_TTL)
    
    return response

