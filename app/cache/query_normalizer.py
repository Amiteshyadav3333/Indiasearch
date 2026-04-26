# app/cache/query_normalizer.py
# 🔤 Query Normalizer — Canonical Key Generator
# ───────────────────────────────────────────────
# Maps semantically equivalent queries to a single cache key.
# "dehradun weather" == "Weather in Dehradun" == "weather dehradun"
# This dramatically reduces redundant API calls.

import re
import unicodedata

# Stopwords to strip from queries to build canonical key
_STOPWORDS = {
    "in", "at", "of", "the", "a", "an", "for", "on", "me", "bata", "do",
    "kya", "hai", "ka", "ki", "ke", "aaj", "tell", "about", "show", "get",
    "what", "is", "are", "how", "where", "when", "who", "why",
}

# Intent-specific prefix expansions (for better cache grouping)
_SYNONYMS = {
    "mausam": "weather",
    "temperature": "weather",
    "temp": "weather",
    "forecast": "weather",
    "samachar": "news",
    "khabar": "news",
    "breaking": "news",
    "ipl": "cricket ipl",
    "sensex": "finance sensex",
    "nifty": "finance nifty",
}

def normalize_query(query: str) -> str:
    """
    Converts a raw user query into a stable canonical key.
    Steps:
      1. Lowercase + unicode normalize
      2. Remove punctuation
      3. Apply synonym expansion
      4. Remove stopwords
      5. Sort terms for order-independence (only for short queries)
      6. Return deduplicated, joined key
    """
    # Step 1: Lowercase + normalize unicode
    q = unicodedata.normalize("NFKC", query.lower().strip())

    # Step 2: Remove punctuation (keep alphanumeric + spaces)
    q = re.sub(r"[^\w\s]", " ", q)
    q = re.sub(r"\s+", " ", q).strip()

    # Step 3: Apply synonym expansion
    words = q.split()
    expanded = []
    for w in words:
        expanded.extend(_SYNONYMS.get(w, w).split())

    # Step 4: Remove stopwords
    filtered = [w for w in expanded if w not in _STOPWORDS]
    if not filtered:
        filtered = expanded  # fallback if all words were stopwords

    # Step 5: For short queries (<=4 words), sort terms to handle order variation
    # "weather delhi" == "delhi weather"
    if len(filtered) <= 4:
        filtered = sorted(set(filtered))
    else:
        # For longer queries, preserve order but deduplicate
        seen = set()
        deduped = []
        for w in filtered:
            if w not in seen:
                seen.add(w)
                deduped.append(w)
        filtered = deduped

    return " ".join(filtered)


def get_dynamic_ttl(intent: str, query: str) -> int:
    """
    Freshness Buckets: Return appropriate TTL based on query type.
    
    - News/Sports/Finance/Weather: Short TTL (fresh content)
    - Static/General: Long TTL (stable content)
    """
    q = query.lower()
    
    # Very short TTL for real-time data
    if intent in ("sports", "finance"):
        return 30  # 30 seconds (live scores, stock prices)
    
    if intent == "weather":
        return 600  # 10 minutes
    
    if intent == "news" or any(k in q for k in ["latest", "today", "aaj", "breaking", "live"]):
        return 180  # 3 minutes
    
    if intent == "ai":
        return 1800  # 30 minutes (AI answers are expensive)
    
    # Static general queries (Wikipedia facts, brand sites etc.)
    return 600  # 10 minutes default (was 5 min before)


def get_hot_query_ttl(query: str) -> int:
    """
    For warming the hot query cache — longer TTL since these are
    popular queries that are expensive to compute.
    """
    return 3600  # 1 hour for hot queries
