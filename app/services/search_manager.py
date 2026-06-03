# app/services/search_manager.py
# 🧠 INTELLIGENT SEARCH BRAIN — Orchestrator & Multi-Level Pipeline
# ──────────────────────────────────────────────────────────────
# 1. Intent Detection (News, Weather, Sports, Finance, AI)
# 2. Level 0: Redis Cache Hit
# 3. Level 1: Parallel (Local Index + DDG + Yahoo)
# 4. Level 2: Deduplication & Fresh Indexing
# 5. Level 3: Paid fallback chain (Bing first, Serper last-resort with 80/day cap)
# ──────────────────────────────────────────────────────────────

import asyncio
import logging
import time
import re
from datetime import datetime

from app.cache.cache_manager import CacheManager, SEARCH_TTL
from app.cache.query_normalizer import normalize_query, get_dynamic_ttl
from app.cache import hot_query_store
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
    wiki_service,
    ad_service
)
from app.utils import translator

logger = logging.getLogger(__name__)

# ── Tunables ──────────────────────────────────────────────
PARALLEL_TIMEOUT    = 3.0    # total timeout for free sources
MIN_QUALITY_RESULTS = 5      # fallback to Bing if below this
MAX_WEB_RESULTS     = 10
# ──────────────────────────────────────────────────────────

def build_ai_sources(results: list, limit: int = 8) -> list:
    """
    Create compact, clickable source metadata for the AI answer card.
    Keeps AI mode useful without changing the normal search result flow.
    """
    sources = []
    seen_urls = set()

    for item in results:
        url = (item.get("url") or "").strip()
        title = (item.get("title") or "").strip()

        if not url.startswith(("http://", "https://")) or not title:
            continue
        if url in seen_urls:
            continue

        seen_urls.add(url)
        host = re.sub(r"^www\.", "", re.sub(r"^https?://", "", url).split("/")[0])
        sources.append({
            "title": title,
            "url": url,
            "host": host,
            "snippet": (item.get("snippet") or item.get("content") or "")[:220],
            "source": item.get("source") or host,
            "image": item.get("image") or item.get("thumbnail") or item.get("thumbnailUrl") or item.get("image_url") or "",
        })

        if len(sources) >= limit:
            break

    return sources

def normalize_media_result(item: dict, media_type: str) -> dict:
    normalized = dict(item or {})
    if media_type == "image":
        image_url = normalized.get("image") or normalized.get("url") or normalized.get("thumbnail") or ""
        normalized["url"] = image_url
        normalized["image"] = image_url
        normalized.setdefault("title", "Image Result")
        normalized.setdefault("snippet", normalized.get("source_url") or normalized.get("source") or "Image")
    elif media_type == "video":
        url = normalized.get("url") or normalized.get("content") or normalized.get("href") or ""
        image_url = normalized.get("image") or normalized.get("thumbnail") or ""
        if not image_url:
            yt_id = extract_youtube_id(url)
            if yt_id:
                image_url = f"https://i.ytimg.com/vi/{yt_id}/hqdefault.jpg"
        normalized["url"] = url
        normalized["image"] = image_url
        normalized.setdefault("title", "Video Result")
        normalized.setdefault("snippet", normalized.get("publisher") or normalized.get("duration") or "Video")
    return normalized

def extract_youtube_id(url: str) -> str:
    if not url:
        return ""
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{6,})",
        r"youtube\.com/embed/([A-Za-z0-9_-]{6,})",
        r"youtube\.com/shorts/([A-Za-z0-9_-]{6,})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""

def clean_image_query(query: str) -> str:
    cleaned = re.sub(
        r"\b(picture|pictures|image|images|photo|photos|pic|pics|wallpaper|wallpapers|photograph|img|show me|dikhao)\b",
        " ",
        query,
        flags=re.IGNORECASE
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or query

async def resilient_web_results(query: str, max_results: int = MAX_WEB_RESULTS) -> list:
    tasks = [
        asyncio.create_task(duckduckgo_client.search(query, max_results=max_results)),
        asyncio.create_task(yahoo_client.search(query, max_results=max_results)),
        asyncio.create_task(google_client.search(query, max_results=max_results)),
        asyncio.create_task(api_client.search(query, max_results=max_results)),
    ]
    done, pending = await asyncio.wait(tasks, timeout=PARALLEL_TIMEOUT + 2)
    collections = []
    for task in pending:
        task.cancel()
    for task in done:
        try:
            result = await task
            if result:
                collections.append(result)
        except Exception as e:
            logger.error(f"[Brain] Resilient web fallback error: {e}")
    return merge_service.merge_and_deduplicate(collections)

async def identify_intent(query: str) -> str:
    """
    The 'Brain' element: Understands what the user is asking.
    Categories: news, weather, sports, finance, ai, general
    """
    q = query.lower().strip()
    
    # Image Intent
    if any(k in q for k in ["picture", "image", "photo", "pic", "wallpaper", "photograph", "img"]):
        return "images"
    
    # AI Mode Intent
    
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
    # Nutrition Intent
    if any(k in q for k in ["nutrition", "calories", "protein", "diet", "food info"]):
        return "nutrition"
        
    # Sarkari Intent
    if any(k in q for k in ["sarkari", "gov.in", "government scheme", "pm yojana", "sarkari yojana"]):
        return "sarkari"

    # Jobs Intent
    if any(k in q for k in ["jobs", "vacancy", "recruitment", "naukri", "hiring"]):
        return "jobs"

    # Mandi Intent
    if any(k in q for k in ["mandi", "crop price", "gehu ka bhav", "chawal price", "fasal"]):
        return "mandi"

    # IRCTC Intent
    if any(k in q for k in ["irctc", "pnr status", "train status", "train running"]):
        return "irctc"

    # Aadhaar/PAN Intent
    if any(k in q for k in ["aadhaar", "pan card", "uidai", "nsdl", "income tax"]):
        return "aadhaar"

    # Jugaad/Local Intent
    if any(k in q for k in ["jugaad", "repair shop", "mechanic near me", "electrician near me", "plumber", "business", "startup", "market", "shop", "showroom", "factory"]):
        return "jugaad"

    # Courts Intent
    if any(k in q for k in ["court case status", "ecourts", "high court", "supreme court status"]):
        return "courts"
    
    return "general"

def get_direct_hit(query: str) -> list:
    """
    Returns a 'Direct Hit' result if the query looks like a domain or major brand.
    """
    q = query.lower().strip()
    
    # Custom About IndiaSearch
    if q in ["about indiasearch", "who created indiasearch", "indiasearch", "founder of indiasearch", "indiasearch team"]:
        return [{
            "title": "About IndiaSearch 🇮🇳",
            "url": "https://indiasearch.site",
            "snippet": "IndiaSearch was created by Amitesh Kumar Yadav and students of Gurukul Kangri University. Yeh platform specially India ke local businesses ko badhawa dene ke liye design kiya gaya hai, aur jobs search ke liye ise specially optimize kiya gaya hai. We offer multiple services including our AI search engine, downloader.indiasearch, and chat.indiasearch.site. Built with love in India.",
            "source": "direct_hit",
            "image": "about-indiasearch.jpg", # The user will upload this picture to frontend
            "_boost": 100
        }]
    
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

async def run_parallel_pipeline(query: str, page: int = 1, filter: str = "all", lang: str = "en", force_ai: bool = False, pdf_content: str = None, age_verified: bool = False, advanced_mode: bool = False, history: list = None, lat: float = None, lon: float = None, limit: int = 10) -> dict:
    """
    Master Orchestrator implementing the user's requested architecture.
    """
    start_time = time.time()
    language_names = {
        "en": "English", "hi": "Hindi", "as": "Assamese", "bn": "Bengali",
        "brx": "Bodo", "doi": "Dogri", "gu": "Gujarati", "kn": "Kannada",
        "ks": "Kashmiri", "gom": "Konkani", "mai": "Maithili", "ml": "Malayalam",
        "mni": "Manipuri", "mr": "Marathi", "ne": "Nepali", "or": "Odia",
        "pa": "Punjabi", "sa": "Sanskrit", "sat": "Santali", "sd": "Sindhi",
        "ta": "Tamil", "te": "Telugu", "ur": "Urdu", "bho": "Bhojpuri"
    }
    output_language = language_names.get(lang, lang or "English")
    
    # ── Step 0: Translate if needed ────────────────────────
    en_query, detected_lang = translator.translate_query_to_english(query)
    
    # ── Adult Content Check ────────────────────────────────
    if not age_verified:
        adult_keywords = ["porn", "sex", "xxx", "xvideos", "pornhub", "xhamster", "nude", "brazzers", "desi bhabhi"]
        if any(keyword in en_query.lower() for keyword in adult_keywords):
            return {
                "error": "Adult content detected.",
                "requires_age_verification": True
            }
    
    # ── Step 1: Identify Intent ────────────────────────────
    intent = await identify_intent(en_query)
    
    # Map explicit filters to intent
    filter_intent_map = {
        "news": "news", "weather": "weather", "score": "sports", 
        "stock": "finance", "finance": "finance", "sarkari": "sarkari",
        "jobs": "jobs", "mandi": "mandi", "irctc": "irctc",
        "aadhaar": "aadhaar", "jugaad": "jugaad", "courts": "courts",
        "nutrition": "nutrition"
    }
    if filter in filter_intent_map:
        intent = filter_intent_map[filter]
        
    if advanced_mode: force_ai = True
    if force_ai: intent = "ai"
    
    # ── Modify Query Based on Restricted Filters ───────────
    if intent == "sarkari" or filter == "sarkari":
        en_query = f"{en_query} (site:gov.in OR site:nic.in OR site:india.gov.in)"
    elif intent == "jobs" or filter == "jobs":
        en_query = f"{en_query} jobs (site:naukri.com OR site:linkedin.com/jobs OR site:sarkariresult.com)"
    elif intent == "courts" or filter == "courts":
        en_query = f"{en_query} (site:ecourts.gov.in OR site:indiancourts.nic.in)"
    elif intent == "aadhaar" or filter == "aadhaar":
        en_query = f"{en_query} (site:uidai.gov.in OR site:incometax.gov.in)"
    elif intent == "irctc" or filter == "irctc":
        en_query = f"{en_query} (site:irctc.co.in OR site:indianrail.gov.in)"
    
    # ── Step 1.2: General India Context ───────────────────
    local_keywords = ["near me", "nearby", "around me", "in my city", "local"]
    is_local_query = any(k in en_query.lower() for k in local_keywords) or intent in ["jugaad", "weather"]

    if intent == "general" and not is_local_query:
        # Subtle boost for general queries to prefer Indian content
        if "india" not in en_query.lower():
            en_query_for_web = f"{en_query} India"
        else:
            en_query_for_web = en_query
    else:
        en_query_for_web = en_query

    logger.info(f"[Brain] Query: {query!r} | Intent: {intent} | Detected Lang: {detected_lang} | Output Lang: {output_language} | Loc: {lat},{lon}")
    image_query_for_web = clean_image_query(en_query_for_web)

    # ── Step 1.5: Location Enhancement ────────────────────
    if is_local_query and lat and lon:
        # For local queries, we want to prioritize results from the user's vicinity.
        # We'll append a "near [lat, lon]" hint to the query for the web search engines.
        # If in advanced mode, we try to be even more specific.
        
        location_hint = f"{lat},{lon}"
        
        # Try to get city name for better search (Mocking a simple lookup or using coords)
        # In a real-world scenario, we'd use a geocoding service here.
        # For now, we'll use the coordinates which most search engines understand.
        
        if advanced_mode:
            en_query = f"{en_query} in my local market near {location_hint}"
        else:
            en_query = f"{en_query} near {location_hint}"
            
        logger.info(f"[Brain] Local enhancement triggered: {en_query}")

    # ── Step 2: Normalize query + Cache Check ──────────────
    # Normalize: "Weather in Delhi" == "delhi weather" → same cache key
    normalized = normalize_query(en_query)
    # Round lat/lon to 2 decimal places (approx 1km accuracy) for cache stability
    loc_suffix = f":{round(lat, 2)}:{round(lon, 2)}" if lat and lon else ""
    cache_key = CacheManager.make_key("brain:search:v7", detected_lang, output_language, normalized, page, intent, filter, "advanced" if advanced_mode else "standard", limit) + loc_suffix
    
    # Record this query for hot cache warming
    hot_query_store.record_query(normalized)

    cached = CacheManager.get(cache_key)
    if cached:
        cached["from_cache"] = True
        cached["took_ms"] = round((time.time() - start_time) * 1000, 1)
        logger.info(f"[Brain] ✅ Cache HIT: {normalized!r}")
        return cached

    results = []
    sources_used = []
    special_data = None

    # ── Level 1: Intent-Specific Data Fetch ───────────────
    tasks = []
    image_tasks = []

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
    dedicated_api_filter = filter in ["weather", "score", "stock", "finance"]

    if intent == "images" and filter == "all":
        # Smart Image Gallery for "All" tab when user asks for pictures
        logger.info("[Brain] Image intent detected in 'All' filter. Fetching top images.")
        image_tasks.append(asyncio.create_task(api_client.search_images(image_query_for_web, max_results=8)))
        image_tasks.append(asyncio.create_task(duckduckgo_client.search_images(image_query_for_web, max_results=8)))
        image_tasks.append(asyncio.create_task(yahoo_client.search_images(image_query_for_web, max_results=8)))

    if filter == "news":
        logger.info("[Brain] News filter active. Using news API plus web fallback.")
        tasks.append(asyncio.create_task(news_service.fetch_news(en_query_for_web)))
    elif dedicated_api_filter:
        logger.info(f"[Brain] Dedicated API filter active: {filter}. Skipping generic web search.")
    elif filter == "images":
        # Multi-source image search so the tab still works if a paid API/key is unavailable.
        tasks.append(asyncio.create_task(api_client.search_images(image_query_for_web, max_results=MAX_WEB_RESULTS)))
        tasks.append(asyncio.create_task(duckduckgo_client.search_images(image_query_for_web, max_results=MAX_WEB_RESULTS)))
        tasks.append(asyncio.create_task(yahoo_client.search_images(image_query_for_web, max_results=MAX_WEB_RESULTS)))
    elif filter == "videos":
        # Multi-source video search with thumbnail normalization.
        tasks.append(asyncio.create_task(api_client.search_videos(en_query_for_web, max_results=MAX_WEB_RESULTS)))
        tasks.append(asyncio.create_task(duckduckgo_client.search_videos(en_query_for_web, max_results=MAX_WEB_RESULTS)))
    else:
        # 1. Local Elasticsearch
        tasks.append(asyncio.create_task(ElasticClient.search_async(en_query, max_results=MAX_WEB_RESULTS)))
        
        # 2. DuckDuckGo (Free Web)
        tasks.append(asyncio.create_task(duckduckgo_client.search(en_query_for_web, max_results=MAX_WEB_RESULTS)))
        
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

    done, pending = await asyncio.wait(tasks, timeout=PARALLEL_TIMEOUT) if tasks else (set(), set())
    
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

    # Process Smart Images if any
    top_images = []
    if image_tasks:
        img_done, img_pending = await asyncio.wait(image_tasks, timeout=PARALLEL_TIMEOUT)
        img_collections = []
        for t in img_done:
            try:
                r = await t
                if r: img_collections.append(r)
            except: pass
        for t in img_pending: t.cancel()
        
        if img_collections:
            flat_imgs = [item for sublist in img_collections for item in sublist]
            top_images = [normalize_media_result(img, "image") for img in flat_imgs][:12]

    # Cancel slow tasks
    for task in pending: task.cancel()

    # ── Level 3: Merge & Deduplicate ──────────────────────
    merged_results = merge_service.merge_and_deduplicate(search_collections)
    if filter == "images":
        merged_results = [normalize_media_result(r, "image") for r in merged_results]
    elif filter == "videos":
        merged_results = [normalize_media_result(r, "video") for r in merged_results]
    filtered_results = merge_service.filter_results(merged_results)
    
    # Track sources from merged
    for r in filtered_results:
        src = r.get("source")
        if src and src not in sources_used: sources_used.append(src)

    # ── Level 4: News & Dedicated Filter Fallbacks ─────────
    if filter == "news" and len(filtered_results) < MIN_QUALITY_RESULTS:
        fallback_news = await resilient_web_results(f"{en_query} latest news India", MAX_WEB_RESULTS)
        if fallback_news:
            filtered_results = merge_service.merge_and_deduplicate([filtered_results, fallback_news])
            for r in filtered_results:
                r["is_news"] = True

    if dedicated_api_filter and len(filtered_results) < 3:
        fallback_query = {
            "weather": f"{en_query} weather forecast",
            "score": f"{en_query} live cricket score",
            "stock": f"{en_query} stock price market",
            "finance": f"{en_query} stock price market",
        }.get(filter, en_query)
        fallback_results = await resilient_web_results(fallback_query, MAX_WEB_RESULTS)
        if fallback_results:
            filtered_results = merge_service.merge_and_deduplicate([filtered_results, fallback_results])

    # ── Level 5: Rank first, THEN check quality ──────────
    final_ranked = ranking_service.rank(filtered_results, en_query)

    # ── Level 5.5: Paid Fallback Chain — Only if quality is insufficient ──
    # quality_check reads _rank_score which is set by rank(), so must come AFTER ranking
    quota = api_client.get_quota_status()
    local_quality_ok = ranking_service.quality_check(final_ranked, min_results=MIN_QUALITY_RESULTS)
    
    if not local_quality_ok and intent not in ["weather", "sports", "finance"] and not dedicated_api_filter:
        logger.info(f"[Brain] Local quality insufficient ({len(final_ranked)} results). Triggering paid API fallback.")
        api_res = await api_client.search(en_query, max_results=MAX_WEB_RESULTS)
        if api_res:
            sources_used.append("fallback_api")
            for r in api_res:
                src = r.get("source")
                if src and src not in sources_used:
                    sources_used.append(src)
            combined = merge_service.merge_and_deduplicate([final_ranked, api_res])
            final_ranked = ranking_service.rank(combined, en_query)
            quota = api_client.get_quota_status()
        else:
            logger.warning("[Brain] Paid fallback returned no results. Staying with free results.")
    else:
        if local_quality_ok:
            logger.info(f"[Brain] ✅ Local results sufficient ({len(final_ranked)}). Skipping paid API.")
    
    # ASYNC TASK: Index fresh results in background for future fast search
    if filtered_results:
        # Don't wait for indexing to finish to respond to user
        asyncio.create_task(index_service.index_results_async(filtered_results))

    # ── Level 6: AI Summary (Google-like AI Overview) ─────
    ai_summary = None
    if force_ai or intent == "ai" or (page == 1 and not dedicated_api_filter):
        ai_summary = await asyncio.to_thread(
            ai_service.generate_ai_summary, 
            query=query, 
            docs=final_ranked, 
            ai_mode=True, 
            lang=output_language,
            pdf_content=pdf_content,
            intent=("advanced" if advanced_mode else intent),
            history=history
        )

    # ── Level 7: Retrieve Knowledge Panel ────────
    knowledge_panel = None
    if kp_task:
        try:
            knowledge_panel = await kp_task
        except:
            pass

    # ── Level 0: Hardcoded Brand Logic (Amitesh Kumar Yadav) ──
    brand_keywords = ["founder", "creator", "owner", "developed by", "made by", "who made", "kisne banaya", "about", "team"]
    q_low = query.lower()
    if ("indiasearch" in q_low or "india search" in q_low) and any(k in q_low for k in brand_keywords):
        knowledge_panel = {
            "title": "Amitesh Kumar Yadav",
            "subtitle": "Founder & Developer of IndiaSearch",
            "snippet": "IndiaSearch was created by Amitesh Kumar Yadav and students of Gurukul Kangri University. Yeh platform specially India ke local businesses ko badhawa dene ke liye design kiya gaya hai, aur jobs search ke liye ise specially optimize kiya gaya hai. We offer multiple services including our AI search engine, downloader.indiasearch, and chat.indiasearch.site. Built with love in India.",
            "image": "/about-indiasearch.jpg",
            "url": "https://chat.indiasearch.site"
        }

    # Final pagination
    if advanced_mode or intent == "nutrition":
        paginated = final_ranked[:4] # Only 4 highly accurate links for specialized searches
    else:
        offset = (page - 1) * limit
        paginated = final_ranked[offset : offset + limit]

    took_ms = round((time.time() - start_time) * 1000, 1)
    
    response = {
        "results": paginated,
        "intent": intent,
        "ad_slots": ad_service.build_ad_slots(query=query, intent=intent, search_filter=filter),
        "special_data": special_data,
        "top_images": top_images,
        "knowledge_panel": knowledge_panel,
        "ai_summary": ai_summary if filter not in ["images", "videos"] else None,
        "ai_sources": build_ai_sources(final_ranked) if filter not in ["images", "videos"] and page == 1 else [],
        "total": len(final_ranked),
        "sources_used": sources_used,
        "quota_status": quota,
        "took_ms": took_ms,
        "from_cache": False
    }

    # ── Step 7: Cache with dynamic TTL ────────────────────
    dynamic_ttl = get_dynamic_ttl(intent, en_query)
    CacheManager.set(cache_key, response, ttl=dynamic_ttl)
    logger.info(f"[Brain] Cached response for {normalized!r} | TTL={dynamic_ttl}s")
    
    return response
