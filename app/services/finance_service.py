# app/services/finance_service.py
import os
import aiohttp
import logging

logger = logging.getLogger(__name__)

async def fetch_stock(query: str) -> dict:
    """
    Fetches real-time stock data from Alpha Vantage.
    """
    api_key = os.getenv("ALPHAVANTAGE_API_KEY")
    if not api_key:
        return None
        
    symbol_map = {
        "nifty": "NSE:NIFTY50",
        "sensex": "BSE:SENSEX",
        "reliance": "RELIANCE.BSE",
        "tcs": "TCS.BSE",
        "hdfc": "HDFCBANK.BSE",
        "sbi": "SBIN.BSE"
    }
    
    symbol = "NSE:NIFTY50" # Default for generic "Stock data" query
    q_low = query.lower()
    for k, v in symbol_map.items():
        if k in q_low:
            symbol = v
            break
            
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                data = await resp.json()
                quote = data.get("Global Quote", {})
                if quote and "05. price" in quote:
                    return {
                        "type": "finance",
                        "symbol": quote.get("01. symbol"),
                        "price": quote.get("05. price", "0.0"),
                        "change": quote.get("09. change", "0.0"),
                        "change_percent": quote.get("10. change percent", "0%"),
                        "high": quote.get("03. high", "0.0"),
                        "low": quote.get("04. low", "0.0"),
                        "volume": quote.get("06. volume", "0"),
                        "last_trading_day": quote.get("07. latest trading day", "")
                    }
    except Exception as e:
        logger.error(f"Finance API error for {symbol}: {e}")
    return None
