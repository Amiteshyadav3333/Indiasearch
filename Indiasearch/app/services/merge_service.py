# app/services/merge_service.py
# 🔗 Merge & Deduplicate Service
# ─────────────────────────────
# Merges results from multiple sources,
# deduplicates by URL, and normalizes fields.

import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def _normalize_url(url: str) -> str:
    """Remove query strings and fragments for dedup comparison."""
    try:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}{p.path}".rstrip("/").lower()
    except Exception:
        return url.lower()


def merge_and_deduplicate(source_lists: list[list]) -> list:
    """
    Merge multiple result lists, deduplicate by normalized URL.
    Earlier sources (higher priority) win duplicates.
    
    Args:
        source_lists: List of result lists. Priority = order (first = highest).
    
    Returns:
        Flattened, deduplicated list of results.
    """
    seen_urls: dict[str, int] = {}  # norm_url → index in output
    merged: list = []

    for source_list in source_lists:
        for result in source_list:
            url = result.get("url", "")
            if not url:
                continue
            norm = _normalize_url(url)
            if norm in seen_urls:
                # Boost score of duplicate (seen in multiple sources = more relevant)
                existing_idx = seen_urls[norm]
                merged[existing_idx]["_boost"] = merged[existing_idx].get("_boost", 0) + 1
            else:
                result["_boost"] = 0
                seen_urls[norm] = len(merged)
                merged.append(result)

    logger.info(f"[Merge] {sum(len(l) for l in source_lists)} raw → {len(merged)} unique results")
    return merged


def filter_results(results: list, min_title_len: int = 5, min_snippet_len: int = 10) -> list:
    """
    Filter out low-quality results:
    - Missing or very short titles
    - Missing URLs
    - Spam/blocked domains
    """
    BLOCKED_DOMAINS = {"pinterest.com", "quora.com/search"}

    filtered = []
    for r in results:
        title = r.get("title", "").strip()
        url = r.get("url", "").strip()
        snippet = r.get("snippet", "").strip()

        if not url or not title:
            continue
        if len(title) < min_title_len:
            continue
        if len(snippet) < min_snippet_len:
            r["snippet"] = ""  # allow empty snippet but keep result

        domain = urlparse(url).netloc.replace("www.", "")
        if domain in BLOCKED_DOMAINS:
            continue

        filtered.append(r)

    logger.info(f"[Merge] After filter: {len(filtered)}/{len(results)} results remain")
    return filtered
