# app/routes/ai_routes.py
# 🤖 AI Routes — Thin Controller
# ----------------------------------------
# Endpoints:
#   POST /api/ai/summary        → AI summary for a search query/URL
#   POST /api/ai/explain        → Explain a concept in Hindi/English
#   GET  /api/ai/knowledge-panel → Wikipedia-style knowledge panel
#
# Business logic lives in: app/services/ai_service.py
# Grok/AI client lives in: app/integrations/grok_client.py

from flask import Blueprint, request
from app.utils.response_formatter import success, error

ai_bp = Blueprint("ai", __name__)


@ai_bp.post("/summary")
def get_summary():
    """Generate AI summary for a query or URL content."""
    # TODO: data = request.get_json()
    # TODO: summary = AIService.summarize(data["query"], data.get("url"))
    return success({"summary": "AI summary stub"})


@ai_bp.post("/explain")
def explain():
    """Explain a concept in simple language."""
    # TODO: data = request.get_json()
    # TODO: explanation = AIService.explain(data["concept"], data.get("lang", "hi"))
    return success({"explanation": "explanation stub"})


@ai_bp.get("/knowledge-panel")
def knowledge_panel():
    """Return Wikipedia-style knowledge panel for an entity."""
    # TODO: q = request.args.get("q")
    # TODO: panel = AIService.get_knowledge_panel(q)
    return success({"panel": None})
