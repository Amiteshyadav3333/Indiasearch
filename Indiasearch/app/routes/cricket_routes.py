# app/routes/cricket_routes.py
# 🏏 Cricket Routes — Thin Controller
# ----------------------------------------
# Endpoints:
#   GET /api/cricket/live       → Live match scores
#   GET /api/cricket/schedule   → Upcoming matches
#   GET /api/cricket/scorecard  → Match scorecard by match ID
#
# Business logic lives in: app/services/cricket_service.py
# API client lives in:     app/integrations/cricket_client.py

from flask import Blueprint, request
from app.utils.response_formatter import success, error

cricket_bp = Blueprint("cricket", __name__)


@cricket_bp.get("/live")
def live_scores():
    """Get live cricket match scores."""
    # TODO: results = CricketService.get_live_scores()
    return success({"matches": []})


@cricket_bp.get("/schedule")
def schedule():
    """Get upcoming cricket match schedule."""
    # TODO: results = CricketService.get_schedule()
    return success({"schedule": []})


@cricket_bp.get("/scorecard")
def scorecard():
    """Get full scorecard for a specific match."""
    # TODO: match_id = request.args.get("match_id")
    # TODO: card = CricketService.get_scorecard(match_id)
    return success({"scorecard": "scorecard stub"})
