# app/routes/finance_routes.py
# 💹 Finance Routes — Thin Controller
# ----------------------------------------
# Endpoints:
#   GET /api/finance/stock      → Stock quote by symbol (NSE/BSE)
#   GET /api/finance/crypto     → Crypto prices
#   GET /api/finance/market     → Market overview (Sensex, Nifty)
#
# Business logic lives in: app/services/finance_service.py
# API client lives in:     app/integrations/alphavantage_client.py

from flask import Blueprint, request
from app.utils.response_formatter import success, error

finance_bp = Blueprint("finance", __name__)


@finance_bp.get("/stock")
def stock_quote():
    """Get stock quote for a symbol (e.g. RELIANCE.BSE)."""
    # TODO: symbol = request.args.get("symbol")
    # TODO: data = FinanceService.get_stock(symbol)
    return success({"stock": "stock stub"})


@finance_bp.get("/crypto")
def crypto_price():
    """Get cryptocurrency price."""
    # TODO: coin = request.args.get("coin", "BTC")
    # TODO: data = FinanceService.get_crypto(coin)
    return success({"crypto": "crypto stub"})


@finance_bp.get("/market")
def market_overview():
    """Get Indian market overview — Sensex, Nifty, etc."""
    # TODO: data = FinanceService.get_market_overview()
    return success({"market": "market overview stub"})
