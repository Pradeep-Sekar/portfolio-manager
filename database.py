import sqlite3
import yfinance as yf
from rich.progress import Progress

def initialize_db():
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock TEXT NOT NULL,
            purchase_date TEXT NOT NULL,
            purchase_price REAL NOT NULL,
            units INTEGER NOT NULL,
            currency TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_stock(stock, purchase_date, purchase_price, units, currency):
    """Adds a stock entry into the database with currency."""
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO portfolio (stock, purchase_date, purchase_price, units, currency)
        VALUES (?, ?, ?, ?, ?)""",
        (stock, purchase_date, purchase_price, units, currency))
    conn.commit()
    conn.close()
    print(f"✅ Stock {stock} ({currency}) added successfully!")

def view_portfolio():
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM portfolio")
    records = cursor.fetchall()
    conn.close()
    return records

def delete_stock(stock_id):
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM portfolio WHERE id = ?", (stock_id,))
    conn.commit()
    conn.close()

import yfinance as yf

def get_live_price(stock_symbol, currency):
    """Fetches the latest stock price with a loading indicator."""
    try:
        with Progress() as progress:
            task = progress.add_task(f"[cyan]Fetching price for {stock_symbol}...", total=100)
            stock = yf.Ticker(stock_symbol)
            stock_info = stock.history(period="1d")

            if stock_info.empty:
                print(f"⚠️ Stock {stock_symbol} is invalid or delisted.")
                return None

            progress.update(task, completed=100)
            live_price = round(stock_info["Close"].iloc[-1], 2)
            
            # Convert USD → INR if needed
            if currency == "INR" and not stock_symbol.endswith(".NS"):
                conversion_rate = get_usd_to_inr()
                return round(live_price * conversion_rate, 2)

            return live_price
    except Exception as e:
        print(f"⚠️ Error fetching live price for {stock_symbol}: {e}")
        return None

import requests

def get_usd_to_inr():
    """Fetches the latest USD to INR conversion rate from an API."""
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        data = response.json()
        return round(data["rates"]["INR"], 2)  # Returns exchange rate (e.g., 83.50)
    except Exception as e:
        print(f"⚠️ Error fetching USD to INR conversion rate: {e}")
        return 83.0  # Default fallback rate

def get_historical_price(stock_symbol, period="1mo"):
    """Fetches historical stock price data for the given period."""
    try:
        stock = yf.Ticker(stock_symbol)
        history = stock.history(period=period)

        if history.empty:
            print(f"⚠️ No historical data found for {stock_symbol}.")
            return None

        return history["Close"]  # Returns the closing price series
    except Exception as e:
        print(f"⚠️ Error fetching historical prices for {stock_symbol}: {e}")
        return None