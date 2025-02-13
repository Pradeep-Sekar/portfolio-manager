import sqlite3
from rich.console import Console

console = Console()
import yfinance as yf
from rich.progress import Progress

import sqlite3

def initialize_db():
    """Creates the database and portfolio table with correct schema."""
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()


    # Fetch the correct name
    name = None
    if investment_type == "Stock":
        name = get_stock_name(symbol)
    elif investment_type == "Mutual Fund":
        name = get_mutual_fund_name(symbol)

    # If name is still None, use 'Unknown'
    if not name:
        name = "Unknown"
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            investment_type TEXT NOT NULL CHECK(investment_type IN ('Stock', 'Mutual Fund')),
            symbol TEXT NOT NULL,
            purchase_date TEXT NOT NULL,
            purchase_price REAL NOT NULL,
            units REAL NOT NULL,
            currency TEXT NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()

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

def add_investment(investment_type, symbol, purchase_date, purchase_price, units, currency):
    """Adds a stock or mutual fund entry into the database with a proper name."""
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO portfolio (investment_type, symbol, name, purchase_date, purchase_price, units, currency)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (investment_type, symbol, name, purchase_date, purchase_price, units, currency))
    conn.commit()
    conn.close()
    print(f"✅ {investment_type} {symbol} ({currency}) added successfully! Name: {name}")

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
            task = progress.add_task("[cyan]Fetching price...", total=100)
            stock = yf.Ticker(stock_symbol)
            stock_info = stock.history(period="1d")

            if stock_info.empty:
                console.print(f"[bold red]⚠️ Stock {stock_symbol} is invalid or delisted.[/]")
                return None

            progress.update(task, completed=100)
            live_price = round(stock_info["Close"].iloc[-1], 2)
            
            # Convert USD → INR if needed
            if currency == "INR" and not stock_symbol.endswith(".NS"):
                conversion_rate = get_usd_to_inr()
                return round(live_price * conversion_rate, 2)

            return live_price
    except Exception as e:
        console.print(f"[bold red]⚠️ Error fetching live price for {stock_symbol}: {e}[/]")
        return None

import requests

def get_usd_to_inr():
    """Fetches the latest USD to INR conversion rate from an API."""
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        data = response.json()
        return round(data["rates"]["INR"], 2)  # Returns exchange rate (e.g., 83.50)
    except Exception as e:
        console.print(f"[bold red]⚠️ Error fetching USD to INR conversion rate: {e}[/]")
        return 83.0  # Default fallback rate

def get_historical_price(stock_symbol, period="1mo"):
    """Fetches historical stock price data for the given period."""
    try:
        stock = yf.Ticker(stock_symbol)
        history = stock.history(period=period)

        if history.empty:
            console.print(f"[bold red]⚠️ No historical data found for {stock_symbol}.[/]")
            return None

        return history["Close"]  # Returns the closing price series
    except Exception as e:
        console.print(f"[bold red]⚠️ Error fetching historical prices for {stock_symbol}: {e}[/]")
        return None

def get_mutual_fund_nav(symbol):
    """Fetches the latest Mutual Fund NAV from AMFI (India Mutual Fund API)."""
    try:
        url = "https://api.mfapi.in/mf/" + symbol
        response = requests.get(url)
        data = response.json()

        if "data" in data and data["data"]:
            latest_nav = float(data["data"][0]["nav"])
            return latest_nav
        else:
            return None  # If NAV not found
    except Exception as e:
        print(f"⚠️ Error fetching NAV for {symbol}: {e}")
        return None
