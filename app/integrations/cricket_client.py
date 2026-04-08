# app/integrations/cricket_client.py
# 🏏 CricAPI / CricketData.org Client
# ----------------------------------------
# Wraps CricAPI (cricapi.com) or CricketData.org REST API.
# API docs: https://www.cricapi.com/
#
# Required env: CRICKET_API_KEY (in .env)

import requests
from app.config.settings import Settings


class CricketClient:
    """CricAPI wrapper for live scores and schedule."""

    BASE_URL = "https://api.cricapi.com/v1"

    @classmethod
    def get_live(cls) -> dict:
        """Fetch currently live matches."""
        # TODO:
        # resp = requests.get(
        #     f"{cls.BASE_URL}/currentMatches",
        #     params={"apikey": Settings.CRICKET_API_KEY, "offset": 0}
        # )
        # resp.raise_for_status()
        # return resp.json()
        raise NotImplementedError("Migrate cricket logic from api.py")

    @classmethod
    def get_schedule(cls) -> dict:
        """Fetch upcoming match schedule."""
        # TODO: endpoint /matches
        raise NotImplementedError

    @classmethod
    def get_scorecard(cls, match_id: str) -> dict:
        """Fetch scorecard for a specific match."""
        # TODO: endpoint /match_scorecard with match_id
        raise NotImplementedError
