import re
from typing import Any


DEMO_ADS = [
    {
        "id": "demo_jobs_001",
        "advertiser": "IndiaSearch Careers",
        "title": "Find verified jobs and internships in India",
        "description": "Explore fresher roles, internships, remote work, and government job updates from one focused career page.",
        "url": "https://indiasearch.site",
        "cta": "Explore jobs",
        "category": "jobs",
        "keywords": ["job", "jobs", "career", "internship", "naukri", "vacancy", "hiring", "recruitment"],
        "placement": "between_results",
    },
    {
        "id": "demo_learning_001",
        "advertiser": "IndiaSearch Learning",
        "title": "Learn AI, Python, and web development",
        "description": "Start skill-based learning with beginner-friendly resources for students and working professionals.",
        "url": "https://chat.indiasearch.site",
        "cta": "Start learning",
        "category": "education",
        "keywords": ["course", "learn", "python", "ai", "coding", "student", "tutorial", "programming"],
        "placement": "between_results",
    },
    {
        "id": "demo_local_001",
        "advertiser": "Local Business Boost",
        "title": "Promote your local business on IndiaSearch",
        "description": "Reach customers searching for shops, services, repairs, showrooms, and businesses near them.",
        "url": "https://indiasearch.site",
        "cta": "Promote business",
        "category": "local",
        "keywords": ["near me", "shop", "business", "repair", "mechanic", "plumber", "electrician", "service", "local"],
        "placement": "between_results",
    },
    {
        "id": "demo_finance_001",
        "advertiser": "Market Research Desk",
        "title": "Track stocks, market news, and finance updates",
        "description": "Follow market movements, stock prices, and business news with quick AI-assisted summaries.",
        "url": "https://indiasearch.site",
        "cta": "View market updates",
        "category": "finance",
        "keywords": ["stock", "share", "market", "nifty", "sensex", "finance", "crypto", "price"],
        "placement": "between_results",
    },
    {
        "id": "demo_food_001",
        "advertiser": "IndiaSearch Nutrition",
        "title": "Scan food and understand nutrition instantly",
        "description": "Use the AI nutrition scanner for calories, protein, carbs, fat, and practical food tips.",
        "url": "https://indiasearch.site",
        "cta": "Try nutrition scan",
        "category": "nutrition",
        "keywords": ["food", "nutrition", "calorie", "calories", "protein", "diet", "fruit", "apple", "dal", "roti"],
        "placement": "between_results",
    },
]

INTENT_CATEGORY_BOOSTS = {
    "jobs": "jobs",
    "finance": "finance",
    "jugaad": "local",
    "nutrition": "nutrition",
    "images": "education",
    "general": "",
}


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def build_ad_slots(query: str, intent: str = "general", search_filter: str = "all", limit: int = 2) -> list[dict[str, Any]]:
    query_text = (query or "").lower()
    query_tokens = _tokens(query_text)
    boosted_category = INTENT_CATEGORY_BOOSTS.get(intent) or INTENT_CATEGORY_BOOSTS.get(search_filter, "")
    scored_ads = []

    for ad in DEMO_ADS:
        score = 0
        keyword_hits = []

        for keyword in ad["keywords"]:
            keyword_lower = keyword.lower()
            if " " in keyword_lower:
                if keyword_lower in query_text:
                    score += 4
                    keyword_hits.append(keyword)
            elif keyword_lower in query_tokens:
                score += 3
                keyword_hits.append(keyword)

        if boosted_category and ad["category"] == boosted_category:
            score += 5

        if score <= 0 and ad["category"] == "local" and any(k in query_text for k in ["near", "nearby", "around"]):
            score += 2

        if score > 0:
            ad_payload = {
                "id": ad["id"],
                "advertiser": ad["advertiser"],
                "title": ad["title"],
                "description": ad["description"],
                "url": ad["url"],
                "cta": ad["cta"],
                "category": ad["category"],
                "placement": ad["placement"],
                "match_score": score,
                "matched_keywords": keyword_hits[:5],
                "disclosure": "Sponsored",
            }
            scored_ads.append(ad_payload)

    scored_ads.sort(key=lambda item: item["match_score"], reverse=True)
    return scored_ads[:limit]
