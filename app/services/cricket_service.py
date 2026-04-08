# app/services/cricket_service.py
import os
import aiohttp
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def fetch_live_score() -> list:
    """
    Fetches real-time live cricket scores.
    """
    api_key = os.getenv("cricketdata_API_KEY")
    if not api_key:
        return None
        
    url = f"https://api.cricapi.com/v1/currentMatches?apikey={api_key}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                data = await resp.json()
                if data.get("status") == "success":
                    matches = data.get("data", [])
                    processed = []
                    now_time = datetime.now().strftime("%I:%M %p")
                    
                    for m in matches:
                        if not m.get("matchStarted"): continue
                        
                        scores = m.get("score", [])
                        live_info = {"r": 0, "w": 0, "o": 0, "inning": "Live"}
                        if scores:
                            s = scores[0]
                            live_info = {
                                "r": s.get("r", 0),
                                "w": s.get("w", 0),
                                "o": s.get("o", 0),
                                "inning": s.get("inning", "Ongoing")
                            }
                        
                        processed.append({
                            "type": "cricket",
                            "name": m.get("name"),
                            "status": m.get("status"),
                            "venue": m.get("venue"),
                            "score": live_info,
                            "updated_at": now_time
                        })
                    return processed[:5]
    except Exception as e:
        logger.error(f"Cricket API error: {e}")
    return None
