# app/integrations/elastic_client.py
# 📦 Elasticsearch Client — Connection & Query Wrapper
# ─────────────────────────────────────────────────────
# Wraps the Elasticsearch Python client.
# Provides: search, index, delete, health-check.
# Falls back gracefully if ES is not available.

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Attempt to import ES client
try:
    from elasticsearch import Elasticsearch
    _ES_AVAILABLE = True
except ImportError:
    _ES_AVAILABLE = False
    logger.warning("[Elastic] elasticsearch-py not installed — search disabled.")


class ElasticClient:
    """Singleton Elasticsearch client wrapper."""

    _client: Optional[object] = None

    @classmethod
    def _build(cls):
        """Create the Elasticsearch connection."""
        url = os.getenv("ELASTICSEARCH_URL", "")
        if not url or not _ES_AVAILABLE:
            return None
        try:
            client = Elasticsearch(url, request_timeout=3)
            if client.ping():
                logger.info(f"[Elastic] Connected to: {url}")
                return client
            else:
                logger.warning("[Elastic] Ping failed — ES unreachable.")
                return None
        except Exception as e:
            logger.error(f"[Elastic] Connection error: {e}")
            return None

    @classmethod
    def get_client(cls):
        """Return a shared Elasticsearch connection (lazy singleton)."""
        if cls._client is None:
            cls._client = cls._build()
        return cls._client

    @classmethod
    def ping(cls) -> bool:
        """Health check — returns True if ES is reachable."""
        client = cls.get_client()
        return bool(client)

    @classmethod
    def search(cls, query: str, index: str = "indiasearch", max_results: int = 10) -> list:
        """
        Execute a full-text search on the given index.
        Returns normalized list of result dicts.
        """
        client = cls.get_client()
        if not client:
            return []
        try:
            body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^3", "content^2", "url"],
                        "type": "best_fields",
                        "fuzziness": "AUTO",
                    }
                },
                "size": max_results,
            }
            resp = client.search(index=index, body=body)
            hits = resp.get("hits", {}).get("hits", [])
            results = []
            for hit in hits:
                src = hit.get("_source", {})
                results.append({
                    "title":   src.get("title", ""),
                    "url":     src.get("url", ""),
                    "snippet": src.get("content", "")[:300],
                    "score":   hit.get("_score", 0),
                    "source":  "elasticsearch",
                })
            logger.info(f"[Elastic] Found {len(results)} hits for: {query!r}")
            return results
        except Exception as e:
            logger.error(f"[Elastic] Query failed: {e}")
            return []

    @classmethod
    def index_doc(cls, doc: dict, doc_id: str = None, index: str = "indiasearch") -> bool:
        """Index a document into Elasticsearch."""
        client = cls.get_client()
        if not client:
            return False
        try:
            client.index(index=index, id=doc_id, body=doc)
            return True
        except Exception as e:
            logger.error(f"[Elastic] Index failed: {e}")
            return False
