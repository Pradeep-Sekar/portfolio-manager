import yfinance as yf
import requests


def get_stock_name(symbol):
    """Fetch the full company name for a stock symbol from Yahoo Finance."""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        return info.get("longName", None)  # Returns the full stock name if available
    except Exception as e:
        print(f"⚠️ Error fetching Stock name for {symbol}: {e}")
        return None

def get_mutual_fund_name(symbol):
    """Fetch the full mutual fund name from AMFI API based on scheme code."""
    try:
        url = f"https://api.mfapi.in/mf/{symbol}"
        response = requests.get(url)
        data = response.json()

        if "meta" in data and "scheme_name" in data["meta"]:
            return data["meta"]["scheme_name"]  # Returns full mutual fund name
        else:
            return None
    except Exception as e:
        print(f"⚠️ Error fetching Mutual Fund name for {symbol}: {e}")
        return None