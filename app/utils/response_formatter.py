# app/utils/response_formatter.py
# 🎯 Response Formatter — Standardized JSON Responses
# ─────────────────────────────────────────────────────
# All endpoints use these helpers to ensure a consistent
# envelope format across the entire API.
#
# Envelope structure:
#   { "status": "ok"|"error", "data": {...}, "meta": {...} }

import time
from flask import jsonify


def success(data=None, meta: dict = None, status: int = 200):
    """Return a standardized success response."""
    resp = {
        "status": "ok",
        "data": data if data is not None else {},
    }
    if meta:
        resp["meta"] = meta
    return jsonify(resp), status


def error(message: str = "An error occurred", code: int = 500, details=None):
    """Return a standardized error response."""
    resp = {
        "status": "error",
        "error": {
            "message": message,
            "code": code,
        }
    }
    if details:
        resp["error"]["details"] = details
    return jsonify(resp), code


def search_response(results: list, query: str, page: int = 1,
                    total: int = None, sources_used: list = None,
                    from_cache: bool = False, took_ms: float = None):
    """
    Specialized formatter for search results.
    Cleans internal scoring fields before sending to client.
    """
    # Strip internal ranking metadata from public response
    clean = []
    for r in results:
        clean.append({
            "title":   r.get("title", ""),
            "url":     r.get("url", ""),
            "snippet": r.get("snippet", ""),
            "source":  r.get("source", ""),
        })

    meta = {
        "query":       query,
        "page":        page,
        "total":       total if total is not None else len(clean),
        "from_cache":  from_cache,
        "sources":     sources_used or [],
    }
    if took_ms is not None:
        meta["took_ms"] = round(took_ms, 1)

    return success(data={"results": clean}, meta=meta)
