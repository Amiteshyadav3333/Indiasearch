# app/workers/tasks.py
# 🧵 Celery Tasks — Async Background Jobs
# ----------------------------------------
# Define all background tasks here.
# Tasks are picked up by the Celery worker process.
#
# Task Registry:
#   crawl_url_task        → Crawl a single URL and index it
#   bulk_crawl_task       → Crawl a list of URLs in parallel
#   index_document_task   → Index a prepared document into Elasticsearch
#   refresh_cache_task    → Pre-warm Redis cache for popular queries
#   reindex_all_task      → Full Elasticsearch reindex (run nightly via cron)

# from app.workers.celery_worker import celery
# from app.services.crawler_service import CrawlerService
# from app.services.index_service import IndexService
# from app.cache.cache_manager import CacheManager
from app.utils.logger import logger


# @celery.task(bind=True, max_retries=3, default_retry_delay=60)
def crawl_url_task(self, url: str):
    """
    Background task: Crawl a URL, extract content, index into Elasticsearch.
    Retries up to 3 times on failure with 60s delay.
    """
    # TODO:
    # try:
    #     doc = CrawlerService.crawl_url(url)
    #     IndexService.index_page(doc)
    #     logger.info(f"Crawled and indexed: {url}")
    # except Exception as exc:
    #     logger.error(f"Crawl failed for {url}: {exc}")
    #     raise self.retry(exc=exc)
    logger.info(f"[STUB] crawl_url_task called for: {url}")


# @celery.task
def index_document_task(doc: dict):
    """Background task: Index a pre-prepared document into Elasticsearch."""
    # TODO: IndexService.index_page(doc)
    logger.info(f"[STUB] index_document_task called for: {doc.get('url')}")


# @celery.task
def refresh_cache_task(queries: list):
    """
    Background task: Pre-warm Redis cache for a list of popular queries.
    Run this periodically (e.g. every 5 min via Celery Beat).
    """
    # TODO:
    # for q in queries:
    #     results = SearchService.web_search(q, bypass_cache=True)
    #     CacheManager.set(CacheManager.make_key("search", q), results, ttl=300)
    logger.info(f"[STUB] refresh_cache_task called for {len(queries)} queries")


# @celery.task
def reindex_all_task():
    """Background task: Full Elasticsearch reindex. Run nightly."""
    # TODO: IndexService.reindex_all()
    logger.info("[STUB] reindex_all_task called")
