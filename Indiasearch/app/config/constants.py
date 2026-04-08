# app/config/constants.py
# ⚙️ Constants — Non-Secret Static Values
# ----------------------------------------
# Use for magic numbers, feature flags, and fixed config.
# For secret/env-based values, use settings.py instead.

# ── Elasticsearch ───────────────────────────────────────────────
ES_INDEX_NAME       = "indiasearch_pages"
ES_MAX_RESULTS      = 10       # Results per page
ES_MIN_SCORE        = 0.3      # Minimum relevance score threshold

# ── Search ──────────────────────────────────────────────────────
SEARCH_PAGE_SIZE    = 10       # Default results per page
SEARCH_MAX_PAGE     = 100      # Max page number allowed
DDG_FALLBACK_MIN    = 3        # Trigger DDG fallback if ES returns < N results

# ── Cache TTLs (seconds) ────────────────────────────────────────
CACHE_TTL_SEARCH    = 300      # 5 min
CACHE_TTL_WEATHER   = 600      # 10 min
CACHE_TTL_CRICKET   = 30       # 30 sec (live scores)
CACHE_TTL_FINANCE   = 60       # 1 min (stock prices)
CACHE_TTL_AI        = 1800     # 30 min (AI summaries)
CACHE_TTL_NEWS      = 300      # 5 min

# ── Rate Limits ─────────────────────────────────────────────────
RATE_LIMIT_SEARCH   = "30/minute"
RATE_LIMIT_AUTH     = "5/minute"
RATE_LIMIT_DEFAULT  = "200/day"

# ── Supported Languages ─────────────────────────────────────────
SUPPORTED_LANGUAGES = ["hi", "en", "bn", "te", "ta", "mr", "gu", "kn", "ml", "pa"]
DEFAULT_LANGUAGE    = "hi"

# ── Pagination ──────────────────────────────────────────────────
DEFAULT_PAGE        = 1
MAX_HISTORY_ITEMS   = 50       # Max search history entries per user

# ── Celery Task Names ───────────────────────────────────────────
TASK_CRAWL_URL      = "app.workers.tasks.crawl_url_task"
TASK_INDEX_DOCUMENT = "app.workers.tasks.index_document_task"
TASK_REFRESH_CACHE  = "app.workers.tasks.refresh_cache_task"
