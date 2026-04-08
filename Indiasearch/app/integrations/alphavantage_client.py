# app/integrations/alphavantage_client.py
# 💹 AlphaVantage Stock API Client
# ----------------------------------------
# Wraps AlphaVantage REST API for stock and crypto data.
# API docs: https://www.alphavantage.co/documentation/
#
# Required env: ALPHAVANTAGE_API_KEY (in .env)

import requests
from app.config.settings import Settings


class AlphaVantageClient:
    """AlphaVantage API wrapper for stocks and crypto."""

    BASE_URL = "https://www.alphavantage.co/query"

    @classmethod
    def get_quote(cls, symbol: str) -> dict:
        """Fetch real-time stock quote."""
        # TODO:
        # params = {
        #     "function": "GLOBAL_QUOTE",
        #     "symbol": symbol,
        #     "apikey": Settings.ALPHAVANTAGE_API_KEY,
        # }
        # resp = requests.get(cls.BASE_URL, params=params)
        # resp.raise_for_status()
        # return resp.json().get("Global Quote", {})
        raise NotImplementedError("Migrate from test_stocks.py / api.py")

    @classmethod
    def get_crypto(cls, coin: str, market: str = "INR") -> dict:
        """Fetch cryptocurrency price."""
        # TODO:
        # params = {
        #     "function": "CURRENCY_EXCHANGE_RATE",
        #     "from_currency": coin,
        #     "to_currency": market,
        #     "apikey": Settings.ALPHAVANTAGE_API_KEY,
        # }
        raise NotImplementedError
