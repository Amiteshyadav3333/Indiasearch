# app/integrations/weather_client.py
# 🌦️ OpenWeatherMap API Client
# ----------------------------------------
# Wraps OpenWeatherMap REST API.
# API docs: https://openweathermap.org/api
#
# Required env: OPENWEATHER_API_KEY (in .env)

import requests
from app.config.settings import Settings


class WeatherClient:
    """OpenWeatherMap API wrapper."""

    BASE_URL = "https://api.openweathermap.org/data/2.5"

    @classmethod
    def get_current(cls, city: str = None, lat: float = None, lon: float = None) -> dict:
        """Fetch current weather from OpenWeatherMap."""
        # TODO:
        # params = {"appid": Settings.OPENWEATHER_API_KEY, "units": "metric"}
        # if city:
        #     params["q"] = city
        # elif lat and lon:
        #     params["lat"] = lat
        #     params["lon"] = lon
        # resp = requests.get(f"{cls.BASE_URL}/weather", params=params)
        # resp.raise_for_status()
        # return resp.json()
        raise NotImplementedError("Migrate from api.py weather logic")

    @classmethod
    def get_forecast(cls, city: str) -> dict:
        """Fetch 5-day weather forecast."""
        # TODO: Similar to get_current but endpoint: /forecast
        raise NotImplementedError
