import sqlite3
from rich.console import Console

console = Console()
import yfinance as yf
from rich.progress import Progress
from fetch_data import get_stock_name, get_mutual_fund_name  # ✅ Import from new file

import sqlite3

def initialize_db():
    """Creates the database and tables with correct schema."""
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

    # Create the goals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            target_amount REAL NOT NULL,
            time_horizon INTEGER NOT NULL,
            priority_level TEXT NOT NULL CHECK(priority_level IN ('High', 'Standard', 'Low', 'Dormant')) DEFAULT 'Standard',
            expected_cagr REAL NOT NULL DEFAULT 12.0,
            goal_creation_date TEXT NOT NULL
        )
    """)

    # Create the goal_investments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goal_investments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER NOT NULL,
            investment_type TEXT NOT NULL CHECK(investment_type IN ('SIP', 'Lumpsum')),
            investment_date TEXT NOT NULL,
            amount REAL NOT NULL,
            recurring INTEGER NOT NULL DEFAULT 0,
            start_date TEXT,
            end_date TEXT,
            FOREIGN KEY(goal_id) REFERENCES goals(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            total_value REAL NOT NULL,
            total_cost REAL NOT NULL,
            profit_loss REAL NOT NULL,
            inr_exposure REAL NOT NULL,
            usd_exposure REAL NOT NULL,
            UNIQUE(date) ON CONFLICT REPLACE
        )
    """)

    # Calculate and store portfolio snapshot
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    
    # Calculate total portfolio value and exposures
    cursor.execute("""
        SELECT p.symbol, p.investment_type, p.purchase_price, p.units, p.currency, ph.price
        FROM portfolio p
        LEFT JOIN (
            SELECT symbol, price 
            FROM price_history 
            WHERE date = ?
        ) ph ON p.symbol = ph.symbol
    """, (today,))
    
    investments = cursor.fetchall()
    
    total_value = 0
    total_cost = 0
    inr_exposure = 0
    usd_exposure = 0
    usd_rate = get_usd_to_inr()
    
    for symbol, inv_type, buy_price, units, currency, current_price in investments:
        if current_price is None:
            continue
            
        cost = buy_price * units
        value = current_price * units
        
        if currency == "USD":
            cost *= usd_rate
            value *= usd_rate
            usd_exposure += value
        else:
            inr_exposure += value
            
        total_cost += cost
        total_value += value
    
    profit_loss = total_value - total_cost
    
    # Store the snapshot
    cursor.execute("""
        INSERT INTO portfolio_history 
        (date, total_value, total_cost, profit_loss, inr_exposure, usd_exposure)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (today, total_value, total_cost, profit_loss, inr_exposure, usd_exposure))
    
    conn.commit()
    conn.close()

def add_investment(investment_type, symbol, purchase_date, purchase_price, units, currency):
    """Adds a stock or mutual fund entry into the database with a proper name, sector, and industry."""
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()

    name, sector, industry = "Unknown", "N/A", "N/A"  # Default values

    # Determine currency based on investment type and symbol
    if investment_type == "Mutual Fund":
        currency = "INR"  # All mutual funds are in INR
        name = get_mutual_fund_name(symbol)
    else:  # For stocks
        currency = "INR" if (symbol.endswith(".NS") or symbol.endswith(".BO")) else "USD"
        name = get_stock_name(symbol)
        
        # Fetch additional stock info using yfinance
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            sector = info.get('sector', 'N/A')
            industry = info.get('industry', 'N/A')
            if not name:  # If name wasn't fetched earlier
                name = info.get('longName', 'Unknown')
        except Exception as e:
            print(f"⚠️ Could not fetch additional info for {symbol}: {e}")

    if not name:
        name = "Unknown"

    cursor.execute("""
        INSERT INTO portfolio (investment_type, symbol, name, sector, industry, purchase_date, purchase_price, units, currency)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (investment_type, symbol, name, sector, industry, purchase_date, purchase_price, units, currency))
    conn.commit()
    conn.close()
    print(f"✅ {investment_type} {symbol} ({currency}) added successfully! Name: {name}")

def view_portfolio():
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, investment_type, symbol, name, sector, industry, purchase_date, purchase_price, units, currency FROM portfolio")
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

def get_portfolio_insights():
    """Calculates portfolio insights including industry and geographic allocation."""
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()
    
    # Get all stocks with their current values
    cursor.execute("""
        SELECT p.symbol, p.industry, p.units, p.currency, ph.price 
        FROM portfolio p
        LEFT JOIN (
            SELECT symbol, price 
            FROM price_history 
            WHERE (symbol, date) IN (
                SELECT symbol, MAX(date) 
                FROM price_history 
                GROUP BY symbol
            )
        ) ph ON p.symbol = ph.symbol
        WHERE p.investment_type = 'Stock'
    """)
    
    stocks = cursor.fetchall()
    conn.close()
    
    # Calculate total portfolio value and industry allocations
    industry_values = {}
    total_portfolio_value = 0
    
    for symbol, industry, units, currency, price in stocks:
        if price:  # Skip if no price available
            value = units * price
            if currency == "USD":
                value *= get_usd_to_inr()  # Convert to INR
                
            industry = industry if industry != "N/A" else "Other"
            industry_values[industry] = industry_values.get(industry, 0) + value
            total_portfolio_value += value
    
    # Calculate percentages and check for over-exposure
    allocations = []
    warnings = []
    for industry, value in industry_values.items():
        percentage = (value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        risk_level = ""
        if percentage > 60:
            risk_level = "⚠️ HIGH RISK"
            warnings.append(f"⚠️ Warning: {industry} represents {percentage:.1f}% of your portfolio. Consider diversifying to reduce risk.")
        elif percentage > 40:
            risk_level = "⚠️ MODERATE RISK"
            warnings.append(f"⚡ Note: {industry} represents {percentage:.1f}% of your portfolio. Consider rebalancing.")
        elif percentage > 20:
            risk_level = "🟡 LOW RISK"
        else:
            risk_level = "✅ DIVERSIFIED"
        allocations.append((industry, value, percentage, risk_level))
    
    # Calculate geographic exposure
    geographic_values = {"INR": 0, "USD": 0}
    for symbol, industry, units, currency, price in stocks:
        if price:
            value = units * price
            if currency == "USD":
                value_inr = value * get_usd_to_inr()
                geographic_values["USD"] += value_inr
            else:
                geographic_values["INR"] += value

    total_geo_value = geographic_values["INR"] + geographic_values["USD"]
    geographic_allocation = []
    for currency, value in geographic_values.items():
        if total_geo_value > 0:
            percentage = (value / total_geo_value) * 100
            geographic_allocation.append((currency, value, percentage))

    return (
        sorted(allocations, key=lambda x: x[2], reverse=True),  # Industry allocations
        warnings,  # Risk warnings
        sorted(geographic_allocation, key=lambda x: x[2], reverse=True)  # Geographic allocation
    )

def record_goal_investment(goal_id, amount, investment_type):
    """Records an investment (SIP or Lumpsum) for a specific goal."""
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()

    investment_date = datetime.datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        INSERT INTO goal_investments (goal_id, investment_type, investment_date, amount)
        VALUES (?, ?, ?, ?)
    """, (goal_id, investment_type, investment_date, amount))

    conn.commit()
    conn.close()

def get_initial_investment(goal_id):
    """Retrieves the initial investment amount for the goal."""
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT amount FROM goal_investments 
        WHERE goal_id = ? ORDER BY investment_date ASC LIMIT 1
    """, (goal_id,))
    result = cursor.fetchone()
    conn.close()

    return result[0] if result else 0

def calculate_required_investment(target_amount, expected_cagr, years_remaining, current_progress):
    """Calculates the additional monthly investment required to meet the goal."""
    future_value_needed = target_amount - current_progress * ((1 + expected_cagr / 100) ** years_remaining)
    monthly_rate = expected_cagr / 100 / 12
    months_remaining = years_remaining * 12
    if monthly_rate == 0:
        return future_value_needed / months_remaining
    else:
        annuity_factor = ((1 + monthly_rate) ** months_remaining - 1) / monthly_rate
        required_monthly_investment = future_value_needed / annuity_factor
        return required_monthly_investment

def view_goal_progress(goal_id):
    """Computes and displays progress towards a specific goal."""
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()

    # Fetch goal details
    cursor.execute("SELECT name, target_amount, time_horizon, expected_cagr, goal_creation_date FROM goals WHERE id = ?", (goal_id,))
    goal = cursor.fetchone()

    if not goal:
        console.print("[bold red]❌ Goal not found.[/]")
        conn.close()
        return

    name, target_amount, time_horizon, expected_cagr, goal_creation_date = goal

    # Calculate years passed
    start_date = datetime.datetime.strptime(goal_creation_date, "%Y-%m-%d")
    today = datetime.datetime.now()
    years_passed = (today - start_date).days / 365.25

    # Fetch total investments for the goal
    cursor.execute("SELECT SUM(amount) FROM goal_investments WHERE goal_id = ?", (goal_id,))
    result = cursor.fetchone()
    current_progress = result[0] or 0

    # Calculate CAGR achieved
    if years_passed > 0 and current_progress > 0:
        initial_investment = get_initial_investment(goal_id)
        cagr_achieved = ((current_progress / initial_investment) ** (1 / years_passed) - 1) * 100
    else:
        cagr_achieved = 0

    # Calculate projected future value
    years_remaining = time_horizon - years_passed
    projected_future_value = current_progress * ((1 + expected_cagr / 100) ** years_remaining)

    conn.close()

    # Display progress and suggestions
    console.print(f"\n[bold cyan]Goal: {name}[/]")
    console.print(f"Target Amount: ₹{target_amount:,.2f}")
    console.print(f"Current Progress: ₹{current_progress:,.2f}")
    console.print(f"Years Passed: {years_passed:.2f}")
    console.print(f"CAGR Achieved: {cagr_achieved:.2f}%")
    console.print(f"Projected Future Value: ₹{projected_future_value:,.2f}")

    if projected_future_value >= target_amount:
        console.print("[bold green]🎉 You are on track to achieve your goal![/]")
    else:
        shortfall = target_amount - projected_future_value
        suggested_sip = calculate_required_investment(target_amount, expected_cagr, years_remaining, current_progress)
        console.print(f"[bold red]⚠️ You are falling behind your goal.[/]")
        console.print(f"Shortfall: ₹{shortfall:,.2f}")
        console.print(f"💡 Suggested Additional SIP: ₹{suggested_sip:,.2f} per month.")

def insert_sample_goals():
    """Inserts sample goals and investments for testing."""
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()

    # Sample goals
    cursor.executemany("""
        INSERT INTO goals (name, target_amount, time_horizon, priority_level, expected_cagr, goal_creation_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        ('Retirement', 10000000, 20, 'High', 12.0, datetime.datetime.now().strftime("%Y-%m-%d")),
        ('Car Purchase', 500000, 3, 'Standard', 10.0, datetime.datetime.now().strftime("%Y-%m-%d")),
    ])

    # Sample investments
    cursor.executemany("""
        INSERT INTO goal_investments (goal_id, investment_type, investment_date, amount)
        VALUES (?, ?, ?, ?)
    """, [
        (1, 'SIP', '2023-01-01', 10000),
        (1, 'SIP', '2023-02-01', 10000),
        (2, 'Lumpsum', '2023-03-15', 200000),
    ])

    conn.commit()
    conn.close()
    console.print("✅ Sample goals and investments inserted successfully!")

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

    # Ensure tables exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            price REAL NOT NULL,
            UNIQUE(symbol, date) ON CONFLICT REPLACE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            total_value REAL NOT NULL,
            total_cost REAL NOT NULL,
            profit_loss REAL NOT NULL,
            inr_exposure REAL NOT NULL,
            usd_exposure REAL NOT NULL,
            UNIQUE(date) ON CONFLICT REPLACE
        )
    """)
    cursor.execute("SELECT symbol, investment_type FROM portfolio")
    records = cursor.fetchall()

    today = datetime.datetime.today().strftime("%Y-%m-%d")

    for symbol, investment_type in records:
        try:
            # Get the price based on investment type
            if investment_type == "Mutual Fund" and symbol.isdigit():
                latest_price = get_mutual_fund_nav(symbol)
                if latest_price is None:
                    print(f"⚠️ No NAV data for {symbol}, skipping...")
                    continue
            else:  # Stock
                stock = yf.Ticker(symbol)
                hist = stock.history(period="1d")
                if hist.empty:
                    print(f"⚠️ No price data for {symbol}, skipping...")
                    continue
                latest_price = hist["Close"].iloc[-1]
                # No currency conversion here - just return the raw price

            if latest_price:
                # Get the last recorded price
                cursor.execute("""
                    SELECT price FROM price_history 
                    WHERE symbol = ? 
                    ORDER BY date DESC LIMIT 1
                """, (symbol,))
                last_price = cursor.fetchone()

                # Determine price change indicator with color
                if last_price:
                    last_price = last_price[0]
                    if latest_price > last_price:
                        indicator = "\033[92m🔼\033[0m"  # Green up arrow
                    elif latest_price < last_price:
                        indicator = "\033[91m🔽\033[0m"  # Red down arrow
                    else:
                        indicator = "⚫"  # Neutral dot
                else:
                    indicator = "🆕"  # New entry

                cursor.execute("""
                    REPLACE INTO price_history (symbol, date, price) VALUES (?, ?, ?)
                """, (symbol, today, latest_price))

                print(f"✅ Recorded {symbol} price: {round(latest_price, 2)} {indicator} on {today}")
        except Exception as e:
            print(f"⚠️ Error fetching price for {symbol}: {e}")

    conn.commit()
    conn.close()
def apply_sips_for_the_month():
    """Applies all active recurring SIPs for the current month by inserting entries into goal_investments."""
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()

    today = datetime.datetime.now().strftime("%Y-%m-%d")

    # Fetch all active recurring SIPs
    cursor.execute("""
        SELECT id, goal_id, amount FROM goal_investments
        WHERE investment_type = 'SIP' AND recurring = 1
    """)
    sips = cursor.fetchall()

    if not sips:
        console.print("[bold yellow]⚠️ No active recurring SIPs found.[/]")
        conn.close()
        return

    for sip_id, goal_id, amount in sips:
        # Check if the goal is not dormant
        cursor.execute("SELECT priority_level FROM goals WHERE id = ?", (goal_id,))
        priority_level = cursor.fetchone()
        if priority_level and priority_level[0] == 'Dormant':
            continue  # Skip dormant goals

        # Insert a new investment record for this month's SIP
        cursor.execute("""
            INSERT INTO goal_investments (goal_id, investment_type, investment_date, amount, recurring)
            VALUES (?, 'SIP', ?, ?, 0)
        """, (goal_id, today, amount))
        console.print(f"✅ Applied SIP of ₹{amount:.2f} for goal ID {goal_id}.")

    conn.commit()
    conn.close()

def view_historical_performance():
    """Retrieves historical portfolio performance data."""
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            date,
            total_value,
            total_cost,
            profit_loss,
            inr_exposure,
            usd_exposure
        FROM portfolio_history
        ORDER BY date DESC
        LIMIT 30   
    """)
    
    history = cursor.fetchall()
    conn.close()
    return history
