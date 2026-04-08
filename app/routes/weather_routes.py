# app/routes/weather_routes.py
# 🌦️ Weather Routes — Thin Controller
# ----------------------------------------
# Endpoints:
#   GET /api/weather/current    → Current weather by city/coords
#   GET /api/weather/forecast   → 5-day forecast
#
# Business logic lives in: app/services/weather_service.py
# API client lives in:     app/integrations/weather_client.py

from flask import Blueprint, request
from app.utils.response_formatter import success, error

weather_bp = Blueprint("weather", __name__)


@weather_bp.get("/current")
def current_weather():
    """Get current weather for a city or lat/lon."""
    # TODO: city = request.args.get("city")
    # TODO: lat = request.args.get("lat")
    # TODO: lon = request.args.get("lon")
    # TODO: data = WeatherService.get_current(city=city, lat=lat, lon=lon)
    return success({"weather": "current weather stub"})


@weather_bp.get("/forecast")
def forecast():
    """Get 5-day weather forecast."""
    # TODO: city = request.args.get("city")
    # TODO: data = WeatherService.get_forecast(city)
    return success({"forecast": "forecast stub"})
