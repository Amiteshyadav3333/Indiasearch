# app/services/search_manager.py
# 🔥 MAIN SEARCH ENGINE — Parallel Pipeline + Fallback
# ──────────────────────────────────────────────────────
#
# Full flow:
#   1. Cache check      (Redis/Memory)         → instant hit
#   2. Elasticsearch    (parallel w/ step 3)   → fast index search
#   3. DuckDuckGo + Yahoo (parallel, 2.5s max) → live web
#   4. API fallback     (SerpAPI, rate-limited) → last resort
#   5. Merge → Rank → Filter                   → best results
#   6. Cache final response
#
# This integrates directly with the existing FastAPI main.py.

import asyncio
import logging
import time

from app.cache.cache_manager import CacheManager, SEARCH_TTL
from app.integrations import duckduckgo_client, yahoo_client, api_client
from app.integrations.elastic_client import ElasticClient
from app.services import merge_service, ranking_service
from app.services.api_quota_manager import APIQuotaManager

logger = logging.getLogger(__name__)

# ── Tunables ──────────────────────────────────────────────
PARALLEL_TIMEOUT    = 2.5    # max seconds for DDG + Yahoo combined
MIN_QUALITY_RESULTS = 4      # trigger API fallback if fewer good results
RESULTS_PER_PAGE    = 10
# ──────────────────────────────────────────────────────────


async def run_parallel_pipeline(query: str, page: int = 1, lang: str = "en") -> dict:
    """
    Full parallel search pipeline.
    
    Returns dict:
      results      : list of result dicts (ranked, paginated)
      total        : total result count before pagination
      sources_used : list of source names that contributed
      from_cache   : bool — was this a cache hit?
      took_ms      : float — wall-clock ms
      quota_status : dict — API quota state
    """
    start = time.time()
    cache_key = CacheManager.make_key("search:v2", lang, query, page)

    # ── Step 1: Cache check ────────────────────────────────
    cached = CacheManager.get(cache_key)
    if cached:
        cached["from_cache"] = True
        cached["took_ms"] = round((time.time() - start) * 1000, 1)
        logger.info(f"[SearchManager] ✅ Cache HIT: {query!r}")
        return cached

    # ── Step 2: Elasticsearch (non-blocking, starts now) ──
    sources_used = []
    elastic_results = []

    if ElasticClient.ping():
        try:
            elastic_results = ElasticClient.search(query=query, max_results=RESULTS_PER_PAGE)
            if elastic_results:
                sources_used.append("elasticsearch")
                logger.info(f"[SearchManager] ES: {len(elastic_results)} hits")
        except Exception as e:
            logger.warning(f"[SearchManager] Elasticsearch error: {e}")

    # ── Step 3: DDG + Yahoo in parallel (with timeout) ────
    ddg_results   = []
    yahoo_results = []

    try:
        ddg_task   = asyncio.create_task(duckduckgo_client.search(query, max_results=RESULTS_PER_PAGE))
        yahoo_task = asyncio.create_task(yahoo_client.search(query, max_results=RESULTS_PER_PAGE))

        done, pending = await asyncio.wait(
            [ddg_task, yahoo_task],
            timeout=PARALLEL_TIMEOUT
        )

        # Cancel timed-out tasks
        for task in pending:
            task.cancel()
            logger.info(f"[SearchManager] ⏱️ Task timed out after {PARALLEL_TIMEOUT}s")

        completed_results = []
        for task in done:
            try:
                completed_results.append(await task)
            except Exception as e:
                logger.warning(f"[SearchManager] Task error: {e}")

        if ddg_task in done:
            ddg_results = await ddg_task if ddg_task in done else []
        if yahoo_task in done:
            yahoo_results = await yahoo_task if yahoo_task in done else []

        if ddg_results:
            sources_used.append("duckduckgo")
        if yahoo_results:
            sources_used.append("yahoo")

    except Exception as e:
        logger.error(f"[SearchManager] Parallel DDG/Yahoo error: {e}")

    # ── Merge what we have so far ──────────────────────────
    merged   = merge_service.merge_and_deduplicate([elastic_results, ddg_results, yahoo_results])
    filtered = merge_service.filter_results(merged)
    ranked   = ranking_service.rank(filtered, query)

    # ── Step 4: API fallback (quota-gated) ───────────────
    quota_status = APIQuotaManager.status()
    if not ranking_service.quality_check(ranked, min_results=MIN_QUALITY_RESULTS):
        if APIQuotaManager.can_call():
            logger.info(
                f"[SearchManager] 💰 Weak results ({len(ranked)}) — "
                f"calling paid API (quota: {quota_status['remaining']} left)"
            )
            api_results = await api_client.search(query, max_results=RESULTS_PER_PAGE)
            if api_results:
                sources_used.append("serpapi")
                merged   = merge_service.merge_and_deduplicate([ranked, api_results])
                filtered = merge_service.filter_results(merged)
                ranked   = ranking_service.rank(filtered, query)
                quota_status = APIQuotaManager.status()  # refresh after call
        else:
            logger.warning(
                f"[SearchManager] 🚫 API quota exhausted "
                f"({quota_status['used']}/{quota_status['limit']}). Using best available results."
            )

    # ── Paginate ───────────────────────────────────────────
    offset       = (page - 1) * RESULTS_PER_PAGE
    page_results = ranked[offset: offset + RESULTS_PER_PAGE]

    # Strip internal scoring fields for output
    clean_results = []
    for r in page_results:
        clean_results.append({
            "title":   r.get("title", ""),
            "url":     r.get("url", ""),
            "snippet": r.get("snippet", ""),
            "score":   r.get("score", 1.0),
        })

    took_ms = round((time.time() - start) * 1000, 1)
    logger.info(
        f"[SearchManager] Done — {len(clean_results)} results, "
        f"sources={sources_used}, took={took_ms}ms, quota={quota_status['remaining']} left"
    )

    response = {
        "results":      clean_results,
        "total":        len(ranked),
        "sources_used": sources_used,
        "from_cache":   False,
        "took_ms":      took_ms,
        "quota_status": quota_status,
    }

    # ── Step 6: Cache the result ───────────────────────────
    CacheManager.set(cache_key, response, ttl=SEARCH_TTL)
    return response
