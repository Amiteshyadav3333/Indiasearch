# app/services/ranking_service.py
# ⭐ Ranking Service — Score & Sort Results
# ──────────────────────────────────────────
# Computes a composite relevance score for each result based on:
#   1. Query term match in title/snippet
#   2. Source priority (Elastic > DDG > Yahoo > API)
#   3. Cross-source boost (appeared in multiple sources)
#   4. URL authority signals (known quality domains)
#   5. Elasticsearch native score

import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Higher = better source priority
SOURCE_WEIGHTS = {
    "direct_hit":     5.0,  # Intentional navigation always wins
    "elasticsearch":  1.5,
    "google":         1.4,
    "wikipedia":      1.3,
    "duckduckgo":    1.2,
    "yahoo":         1.0,
    "serpapi":       0.9,   # paid API ironically ranks lower (last resort)
    "memory":        0.5,
    "unknown":       0.8,
}

# Domains we trust more (India-centric + authority sites)
TRUSTED_DOMAINS = {
    "wikipedia.org": 0.3,
    "ndtv.com": 0.2,
    "thehindu.com": 0.2,
    "indiatimes.com": 0.15,
    "bbc.com": 0.25,
    "reuters.com": 0.25,
    "github.com": 0.2,
    "stackoverflow.com": 0.2,
}


def _query_match_score(result: dict, query: str) -> float:
    """Score based on how many query terms appear in title + snippet."""
    terms = re.findall(r"\w+", query.lower())
    if not terms:
        return 0.0
    text = (result.get("title", "") + " " + result.get("snippet", "")).lower()
    matched = sum(1 for t in terms if t in text)
    return matched / len(terms)


def _domain_authority(url: str) -> float:
    """Return a small authority bonus for known trusted domains."""
    try:
        domain = urlparse(url).netloc.replace("www.", "")
        for d, bonus in TRUSTED_DOMAINS.items():
            if domain.endswith(d):
                return bonus
    except Exception:
        pass
    return 0.0


def rank(results: list, query: str) -> list:
    """
    Score and sort results by composite relevance.
    
    Scoring formula:
        score = (query_match * 2.0) 
              + (source_weight)
              + (cross_source_boost * 0.5)
              + (elastic_score * 0.1)   # normalized ES score
              + domain_authority
    """
    max_elastic = max((r.get("score", 0) for r in results), default=1) or 1

    for r in results:
        source = r.get("source", "unknown")
        query_match   = _query_match_score(r, query)
        source_weight = SOURCE_WEIGHTS.get(source, SOURCE_WEIGHTS["unknown"])
        boost         = r.get("_boost", 0) * 0.5
        elastic_norm  = (r.get("score", 0) / max_elastic) * 0.2
        authority     = _domain_authority(r.get("url", ""))

        r["_rank_score"] = (
            query_match   * 2.0
            + source_weight
            + boost
            + elastic_norm
            + authority
        )

    ranked = sorted(results, key=lambda r: r["_rank_score"], reverse=True)
    logger.info(f"[Rank] Sorted {len(ranked)} results for: {query!r}")
    return ranked


def quality_check(results: list, min_results: int = 3) -> bool:
    """
    Returns True if results are 'good enough' (above threshold).
    Used to decide whether API fallback is needed.
    """
    if len(results) < min_results:
        return False
    avg_score = sum(r.get("_rank_score", 0) for r in results) / len(results)
    return avg_score >= 0.5
