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
        "reliance": "RELIANCE.BSE",
        "tcs": "TCS.BSE",
        "infosys": "INFY.BSE",
        "infy": "INFY.BSE",
        "hdfc": "HDFCBANK.BSE",
        "hdfc bank": "HDFCBANK.BSE",
        "sbi": "SBIN.BSE",
        "icici": "ICICIBANK.BSE",
        "axis": "AXISBANK.BSE",
        "itc": "ITC.BSE",
        "wipro": "WIPRO.BSE",
        "apple": "AAPL",
        "tesla": "TSLA",
        "microsoft": "MSFT",
        "google": "GOOGL",
        "amazon": "AMZN"
    }
    
    symbol = "RELIANCE.BSE" # Reliable default for generic "Stock data" query
    q_low = query.lower()
    for k, v in sorted(symbol_map.items(), key=lambda item: len(item[0]), reverse=True):
        if k in q_low:
            symbol = v
            break
    else:
        words = [w.strip(" ,.-").upper() for w in query.split()]
        ticker = next((w for w in words if 1 <= len(w) <= 8 and w.isalpha() and w.lower() not in {"stock", "price", "share"}), "")
        if ticker:
            symbol = ticker
            
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
