# app/services/weather_service.py
import os
import aiohttp
import logging
import re

logger = logging.getLogger(__name__)

async def fetch_weather(query: str) -> dict:
    """
    Fetches real-time weather data.
    """
    api_key = os.getenv("whether_API_KEY")
    if not api_key:
        return None
        
    # Extract city name from query (e.g., "weather in Delhi" -> "Delhi")
    city = re.sub(r"\b(weather|mausam|forecast|temperature|temp)\b", "", query, flags=re.I)
    city = re.sub(r"^\s*(in|for|at)\s+", "", city.strip(), flags=re.I)
    if not city:
        city = "Delhi" # default

    try:
        clean_key = api_key.strip().strip('"')
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={clean_key}&units=metric"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "type": "weather",
                        "city": data.get("name"),
                        "temp": round(data["main"]["temp"]),
                        "feels_like": round(data["main"]["feels_like"]),
                        "humidity": data["main"]["humidity"],
                        "wind": data["wind"]["speed"],
                        "desc": data["weather"][0]["description"].capitalize(),
                        "icon": data["weather"][0]["icon"],
                        "country": data["sys"]["country"]
                    }
    except Exception as e:
        logger.error(f"Weather error for {city}: {e}")
    return None
