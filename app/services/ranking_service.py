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
    "openstreetmap":  2.2,
    "duckduckgo":    1.2,
    "yahoo":         1.0,
    "serpapi":       0.9,   # paid API ironically ranks lower (last resort)
    "memory":        0.5,
    "unknown":       0.8,
}

# Domains we trust more (India-centric + authority sites)
TRUSTED_DOMAINS = {
    "wikipedia.org": 0.3,
    "ndtv.com": 0.4,
    "thehindu.com": 0.4,
    "indiatimes.com": 0.35,
    "indianexpress.com": 0.35,
    "jagran.com": 0.4,
    "amarujala.com": 0.4,
    "dainikbhaskar.com": 0.4,
    "gadgets360.com": 0.3,
    "moneycontrol.com": 0.3,
    "sarkariresult.com": 0.5,
    "upsc.gov.in": 0.5,
    "bbc.com": 0.25,
    "reuters.com": 0.25,
    "github.com": 0.2,
    "stackoverflow.com": 0.2,
}

INDIA_PUBLIC_INTEREST_DOMAINS = (
    "gov.in", "nic.in", "ac.in", "res.in", "org.in", "co.in",
    "uidai.gov.in", "incometax.gov.in", "indianrail.gov.in", "irctc.co.in",
    "ecourts.gov.in", "data.gov.in", "ncs.gov.in", "agmarknet.gov.in",
    "ssc.nic.in", "upsc.gov.in", "cbse.nic.in", "ncert.nic.in",
    "indianexpress.com", "thehindu.com", "ndtv.com", "timesofindia.com",
    "hindustantimes.com", "indiatimes.com", "zeebiz.com", "moneycontrol.com",
    "sarkariresult.com", "freejobalert.com", "sarkari naukri.com", "jobsbank.in",
    "railway recruitment.com", "ssc adda.com", "bankersadda.com",
)

# Indian news domains with high priority
INDIAN_NEWS_DOMAINS = {
    "ndtv.com": 0.5,
    "thehindu.com": 0.5,
    "indianexpress.com": 0.45,
    "timesofindia.com": 0.4,
    "hindustantimes.com": 0.4,
    "indiatimes.com": 0.35,
    "zeebiz.com": 0.35,
    "business-standard.com": 0.35,
    "livemint.com": 0.35,
    "economictimes.indiatimes.com": 0.35,
}

# Indian government/edu domains
INDIAN_GOV_EDU_DOMAINS = {
    "gov.in": 0.8,
    "nic.in": 0.75,
    "ac.in": 0.7,
    "res.in": 0.7,
    "org.in": 0.6,
    "co.in": 0.5,
    "uidai.gov.in": 0.9,
    "incometax.gov.in": 0.9,
    "indianrail.gov.in": 0.85,
    "irctc.co.in": 0.8,
    "ecourts.gov.in": 0.85,
    "data.gov.in": 0.8,
    "ncs.gov.in": 0.8,
    "agmarknet.gov.in": 0.8,
    "ssc.nic.in": 0.85,
    "upsc.gov.in": 0.9,
    "cbse.nic.in": 0.85,
    "ncert.nic.in": 0.85,
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
    """Return a small authority bonus for known trusted domains + Indian TLD boost."""
    score = 0.0
    try:
        domain = urlparse(url).netloc.replace("www.", "").lower()
        
        # 1. Indian TLD Boost (Heavy)
        indian_tlds = [".in", ".gov.in", ".nic.in", ".res.in", ".ac.in", ".co.in", ".org.in", ".gen.in", ".firm.in", ".ind.in", ".net.in"]
        if any(domain.endswith(tld) for tld in indian_tlds):
            score += 0.8
            
        # 2. Known Trusted Domains
        for d, bonus in TRUSTED_DOMAINS.items():
            if domain.endswith(d):
                score += bonus
    except Exception:
        pass
    return score


def _india_relevance(url: str, title: str = "", snippet: str = "") -> float:
    """Promote Indian sources while retaining useful international results."""
    try:
        domain = urlparse(url).netloc.replace("www.", "").lower()
    except Exception:
        domain = ""
    text = f"{title} {snippet}".lower()
    score = 0.0
    
    # 1. Indian TLD boost (Heavy)
    if domain.endswith(".in"):
        score += 1.2
    
    # 2. Indian government/edu domains (Very Heavy)
    for d, bonus in INDIAN_GOV_EDU_DOMAINS.items():
        if domain.endswith(d):
            score += bonus
    
    # 3. Indian news domains (Heavy)
    for d, bonus in INDIAN_NEWS_DOMAINS.items():
        if domain.endswith(d):
            score += bonus
    
    # 4. India terms in text
    india_terms = ("india", "bharat", "भारतीय", "भारत", "indian", "sarkari", "सरकारी", "naukri", "job", "government", "central", "state")
    score += min(0.5, sum(term in text for term in india_terms) * 0.12)
    
    return score


def rank(results: list, query: str, lat=None, lon=None) -> list:
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
        india_signal  = _india_relevance(r.get("url", ""), r.get("title", ""), r.get("snippet", ""))
        distance = r.get("distance_km")
        proximity = max(0.0, 3.0 - min(float(distance), 15.0) * 0.2) if distance is not None else 0.0

        r["_rank_score"] = (
            query_match   * 2.0
            + source_weight
            + boost
            + elastic_norm
            + authority
            + india_signal
            + proximity
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
