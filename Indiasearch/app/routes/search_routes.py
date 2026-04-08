# app/routes/search_routes.py
# 🌐 Search Routes — Thin Controller Layer
# ─────────────────────────────────────────
# Endpoints:
#   GET  /api/search/web        → Web search (main pipeline)
#   GET  /api/search/images     → Image search
#   GET  /api/search/news       → News search
#   GET  /api/search/suggest    → Autocomplete suggestions
#   GET  /api/search/history    → User's search history
#   DELETE /api/search/history  → Clear search history
#
# Business logic lives in: app/services/search_manager.py

from flask import Blueprint, request
from app.utils.response_formatter import success, error, search_response
from app.services.search_manager import run_web_search

search_bp = Blueprint("search", __name__)


@search_bp.get("/web")
def web_search():
    """
    Main web search — full parallel pipeline.
    
    Query params:
      q    : search query (required)
      lang : language code (default: en)
      page : page number (default: 1)
    """
    q    = request.args.get("q", "").strip()
    lang = request.args.get("lang", "en")
    page = int(request.args.get("page", 1))

    if not q:
        return error("Query parameter 'q' is required.", code=400)

    try:
        result = run_web_search(q, page=page, lang=lang)
        return search_response(
            results      = result["results"],
            query        = q,
            page         = page,
            total        = result.get("total", 0),
            sources_used = result.get("sources_used", []),
            from_cache   = result.get("from_cache", False),
            took_ms      = result.get("took_ms"),
        )
    except Exception as e:
        return error(f"Search failed: {str(e)}", code=500)


@search_bp.get("/images")
def image_search():
    """Image search via DuckDuckGo."""
    q = request.args.get("q", "").strip()
    if not q:
        return error("Query 'q' is required.", code=400)

    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            imgs = list(ddgs.images(q, max_results=20))
        results = [
            {
                "title":     i.get("title", ""),
                "url":       i.get("url", ""),
                "image_url": i.get("image", ""),
                "source":    i.get("source", ""),
            }
            for i in imgs
        ]
        return search_response(results=results, query=q)
    except Exception as e:
        return error(f"Image search failed: {str(e)}", code=500)


@search_bp.get("/news")
def news_search():
    """News search via DuckDuckGo news."""
    q = request.args.get("q", "").strip()
    if not q:
        return error("Query 'q' is required.", code=400)

    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            news = list(ddgs.news(q, max_results=15))
        results = [
            {
                "title":   n.get("title", ""),
                "url":     n.get("url", ""),
                "snippet": n.get("body", ""),
                "date":    n.get("date", ""),
                "source":  n.get("source", ""),
            }
            for n in news
        ]
        return search_response(results=results, query=q)
    except Exception as e:
        return error(f"News search failed: {str(e)}", code=500)


@search_bp.get("/suggest")
def autocomplete():
    """Autocomplete / suggest via DuckDuckGo."""
    q = request.args.get("q", "").strip()
    if not q or len(q) < 2:
        return success({"suggestions": []})

    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            suggestions = list(ddgs.suggestions(q))
        phrases = [s.get("phrase", "") for s in suggestions if s.get("phrase")]
        return success({"suggestions": phrases[:10]})
    except Exception:
        return success({"suggestions": []})


@search_bp.get("/history")
def get_history():
    """Get user's search history (requires auth)."""
    # TODO: Integrate with auth middleware and DB
    return success({"history": []})


@search_bp.delete("/history")
def clear_history():
    """Clear user's search history (requires auth)."""
    # TODO: Integrate with auth middleware and DB
    return success({"message": "history cleared"})
