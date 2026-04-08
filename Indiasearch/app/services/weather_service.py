# app/services/weather_service.py
# 🌦️ Weather Service — Weather Business Logic
# ----------------------------------------
# Responsibilities:
#   - Fetch current weather and forecast from OpenWeatherMap
#   - Cache results in Redis (TTL: 10 min)
#   - Format response for frontend display
#
# Depends on:
#   app/integrations/weather_client.py  → OpenWeatherMap API
#   app/cache/cache_manager.py          → Redis


class WeatherService:
    """Handles weather data fetching and caching."""

    @staticmethod
    def get_current(city: str = None, lat: float = None, lon: float = None) -> dict:
        """Get current weather by city name or coordinates."""
        # TODO: Check Redis cache (key: weather:current:{city})
        # TODO: Call WeatherClient.get_current(...)
        # TODO: Cache and return result
        raise NotImplementedError("Migrate weather logic from api.py")

    @staticmethod
    def get_forecast(city: str) -> list:
        """Get 5-day weather forecast."""
        # TODO: Check Redis cache (key: weather:forecast:{city})
        # TODO: Call WeatherClient.get_forecast(city)
        raise NotImplementedError
