import sqlite3
from rich.console import Console

console = Console()
import yfinance as yf
from rich.progress import Progress
from fetch_data import get_stock_name, get_mutual_fund_name  # ✅ Import from new file

import sqlite3

def initialize_db():
    """Creates the database and portfolio table with correct schema."""
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            investment_type TEXT NOT NULL CHECK(investment_type IN ('Stock', 'Mutual Fund')),
            symbol TEXT NOT NULL,
            name TEXT,
            purchase_date TEXT NOT NULL,
            purchase_price REAL NOT NULL,
            units REAL NOT NULL,
            currency TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

def add_investment(investment_type, symbol, purchase_date, purchase_price, units, currency):
    """Adds a stock or mutual fund entry into the database with a proper name."""
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()

    name = None
    if investment_type == "Stock":
        name = get_stock_name(symbol)
    elif investment_type == "Mutual Fund":
        name = get_mutual_fund_name(symbol)

    if not name:
        name = "Unknown"

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
    cursor.execute("SELECT id, investment_type, symbol, name, purchase_date, purchase_price, units, currency FROM portfolio")
    records = cursor.fetchall()
    conn.close()
    return records

def delete_investment():
    """Deletes a stock or mutual fund from the portfolio."""
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()

    # Show all investments before asking for deletion
    cursor.execute("SELECT id, investment_type, symbol, name FROM portfolio")
    records = cursor.fetchall()

    if not records:
        print("📭 No investments found in your portfolio.")
        conn.close()
        return

    # Display investments
    print("\n📌 Your Portfolio:")
    for stock_id, investment_type, symbol, name in records:
        print(f"[{stock_id}] {investment_type}: {name} ({symbol})")

    try:
        delete_id = int(input("\n🗑 Enter the ID of the stock or mutual fund to delete: ").strip())
        cursor.execute("DELETE FROM portfolio WHERE id = ?", (delete_id,))
        conn.commit()

        if cursor.rowcount > 0:
            print(f"✅ Investment ID {delete_id} deleted successfully!")
        else:
            print(f"⚠️ Investment ID {delete_id} not found.")
    except ValueError:
        print("❌ Invalid input. Please enter a valid numeric ID.")

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
            if stock_symbol.endswith(".NS") or stock_symbol.endswith(".BO"):
                currency = "INR"
            else:
                currency = "USD"

            if currency == "INR":
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

def insert_sample_data():
    """Adds sample stocks & mutual funds for testing."""
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()

    sample_data = [
        ("Stock", "AAPL", "Apple Inc.", "2023-05-10", 150, 10, "USD"),
        ("Stock", "TSLA", "Tesla Inc.", "2022-11-20", 250, 5, "USD"),
        ("Stock", "TCS.NS", "Tata Consultancy Services", "2021-07-15", 3200, 15, "INR"),
        ("Stock", "RELIANCE.NS", "Reliance Industries", "2020-12-05", 2000, 20, "INR"),
        ("Stock", "HDFCBANK.NS", "HDFC Bank Ltd.", "2019-10-30", 1100, 30, "INR"),
        ("Stock", "INFY.NS", "Infosys Ltd.", "2022-06-25", 1450, 25, "INR"),
        ("Stock", "AMZN", "Amazon.com Inc.", "2023-08-12", 3200, 8, "USD"),
        ("Mutual Fund", "120503", "SBI Bluechip Fund - Direct Plan", "2022-01-15", 125, 100, "INR"),
        ("Mutual Fund", "118114", "Axis Growth Opportunities Fund", "2023-03-18", 200, 50, "INR"),
        ("Mutual Fund", "101885", "Nippon India Small Cap Fund", "2021-05-22", 90, 120, "INR"),
    ]

    cursor.executemany("""
        INSERT INTO portfolio (investment_type, symbol, name, purchase_date, purchase_price, units, currency)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, sample_data)

    conn.commit()
    conn.close()
    print("✅ Sample data inserted successfully!")

def create_price_history_table():
    """Creates a table to track price changes over time for investments."""
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Price history table created!")

import yfinance as yf
import datetime

def update_price_history():
    """Fetches the latest price for all stocks & mutual funds and updates history."""
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()

    # Fetch all investment symbols
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            price REAL NOT NULL,
            UNIQUE(symbol, date) ON CONFLICT REPLACE
        )
    """)
    cursor.execute("SELECT symbol, investment_type FROM portfolio")
    records = cursor.fetchall()

    today = datetime.datetime.today().strftime("%Y-%m-%d")

    for symbol, investment_type in records:
        try:
            if investment_type == "Mutual Fund" and symbol.isdigit():
                latest_price = get_mutual_fund_nav(symbol)
                if latest_price is None:
                    print(f"⚠️ No NAV data for {symbol}, skipping...")
                    continue
            else:
                stock = yf.Ticker(symbol)
                hist = stock.history(period="1d")
                if hist.empty:
                    print(f"⚠️ No price data for {symbol}, skipping...")
                    continue
                latest_price = hist["Close"].iloc[-1]

            cursor.execute("""
                REPLACE INTO price_history (symbol, date, price) VALUES (?, ?, ?)
            """, (symbol, today, latest_price))

            print(f"✅ Recorded {symbol} price: {round(latest_price, 2)} on {today}")
        except Exception as e:
            print(f"⚠️ Error fetching price for {symbol}: {e}")

    conn.commit()
    conn.close()
