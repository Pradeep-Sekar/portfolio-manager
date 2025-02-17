import sqlite3
from datetime import datetime
from database import (
    initialize_db, add_investment, view_portfolio, delete_investment,
    get_live_price, get_mutual_fund_nav, get_usd_to_inr, get_historical_price,
    record_goal_investment, view_goal_progress
)
from fetch_data import (get_stock_name, get_mutual_fund_name)
from config import OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY

#print(f"Using OpenAI API Key: {OPENAI_API_KEY[:5]}...")  # Just for verification

from tabulate import tabulate
from rich.console import Console
from rich.table import Table
from rich.text import Text
import npyscreen




console = Console() 

from pick import pick
from datetime import datetime, timedelta

def select_purchase_date():
    """Displays a simple scrollable date picker (last 30 days)."""
    today = datetime.today()
    date_options = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]  # Last 30 days

    selected, index = pick(date_options, "📅 Select Purchase Date:", indicator="➡️")

    return selected  # Return selected date

def main():
    initialize_db()
    while True:
        console.print("\n[bold cyan]📊 Stock Portfolio Manager[/]", style="bold underline")
        console.print("1. [bold]Add Stock[/]")
        console.print("2. [bold]View Portfolio (with Profit/Loss)[/]")
        console.print("3. [bold]Delete Investment[/]")
        console.print("4. [bold]Exit[/]")
        console.print("5. [bold]View Historical Stock Performance[/]")
        console.print("6. [bold]Update Prices (Manual Refresh)[/]")
        console.print("7. [bold]Portfolio Insights[/]")
        console.print("8. [bold]View Historical Performance[/]")
        choice = input("Enter your choice (1-8): ").strip()

        if choice not in ["1", "2", "3", "4", "5", "6", "7", "8"]:
            console.print("[bold red]❌ Invalid choice! Please enter a number between 1 and 9.[/]")
            continue

        if choice == "1":
            while True:  # Loop until a valid input
                console.print("\n[bold cyan]📌 Select Investment Type:[/]")
                console.print("[1] 📈 Stock", style="green")
                console.print("[2] 💰 Mutual Fund", style="magenta")
                investment_choice = input("Enter your choice (1-2): ").strip()

                if investment_choice == "1":
                    investment_type = "Stock"
                elif investment_choice == "2":
                    investment_type = "Mutual Fund"
                else:
                    console.print("❌ [bold red]Invalid choice! Please enter 1 or 2.[/]")
                    continue  # Re-ask the user

                symbol = input("Enter Symbol (e.g., AAPL for stocks, SBI-MF for Mutual Funds): ").strip().upper()
                purchase_date = select_purchase_date()
                if not purchase_date:
                    console.print("❌ [bold red]No date selected. Please select a valid date.[/]")
                    continue

                try:
                    purchase_price = float(input("Enter Purchase Price per Unit: ").strip())
                    units = float(input("Enter Number of Units: ").strip())
                except ValueError:
                    console.print("❌ [bold red]Invalid input! Price must be a number, and units must be a number.[/]")
                    continue

                # Determine currency (Stocks are USD/INR, Mutual Funds are INR)
                currency = "INR" if (symbol.endswith(".NS") or symbol.endswith(".BO")) else "USD"

                # Validate Stocks using `get_live_price()`, Mutual Funds using `get_mutual_fund_nav()`
                if investment_type == "Stock" and get_live_price(symbol, currency) is None:
                    console.print(f"❌ {symbol} is not a valid stock symbol. Please enter a correct ticker.", style="red")
                    continue

                if investment_type == "Mutual Fund" and get_mutual_fund_nav(symbol) is None:
                    console.print(f"❌ {symbol} is not a valid mutual fund symbol. Please enter a correct ticker.", style="red")
                    continue

                add_investment(investment_type, symbol, purchase_date, purchase_price, units, currency)
                break  # Exit loop after successful addition

        elif choice == "2":  # View portfolio with separate Stock & Mutual Fund sections
            records = view_portfolio()
            if records:
                stock_table = Table(title="📈 Stock Portfolio", title_style="bold cyan")
                fund_table = Table(title="💰 Mutual Fund Portfolio", title_style="bold magenta")

                for table in [stock_table, fund_table]:
                    table.add_column("ID", justify="center", style="bold yellow")
                    table.add_column("Symbol", style="bold white")
                    table.add_column("Name", style="bold white")
                    table.add_column("Sector", style="bold blue")
                    table.add_column("Industry", style="bold blue")
                    table.add_column("Purchase Date", justify="center", style="bold white")
                    table.add_column("Buy Price", justify="right", style="green")
                    table.add_column("Units", justify="center", style="cyan")
                    table.add_column("Currency", justify="center", style="magenta")
                    table.add_column("Current Price/NAV", justify="right", style="bold green")
                    table.add_column("Profit/Loss", justify="right", style="bold red")
                    table.add_column("P/L %", justify="right", style="bold cyan")

                total_stock_value = 0
                total_fund_value = 0
                total_invested_stock = 0
                total_invested_fund = 0

                for record in records:
                    stock_id, investment_type, symbol, name, sector, industry, purchase_date, purchase_price, units, currency = record

                    # Ensure name is correctly displayed
                    display_name = symbol  # Use symbol as display name

                    # Ensure name is correctly displayed
                    display_name = name if name and name != symbol else "Unknown"  # Prevents symbol duplication

                    # Fetch the latest price
                    # Get current and previous price
                    if investment_type == "Stock":
                        live_price = get_live_price(symbol, currency)
                    else:
                        live_price = get_mutual_fund_nav(symbol)

                    # Get the previous price from history
                    conn = sqlite3.connect("portfolio.db")
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT price FROM price_history 
                        WHERE symbol = ? 
                        ORDER BY date DESC LIMIT 2
                    """, (symbol,))
                    prices = cursor.fetchall()
                    conn.close()
                    
                    # Determine price change indicator
                    if len(prices) >= 2:
                        prev_price = prices[1][0]  # Second most recent price
                        indicator = "🔼" if live_price > prev_price else "🔽" if live_price < prev_price else "⚫"
                    else:
                        indicator = "🆕"

                    if purchase_price is None:
                        console.print(f"[bold red]⚠️ Purchase price for {symbol} is not available.[/]")
                        continue

                    # Calculate values in the original currency first
                    total_cost = purchase_price * units
                    current_value = (live_price * units) if live_price else 0
                    profit_loss = (current_value - total_cost) if live_price else 0

                    # Convert to INR for totals
                    conversion_rate = get_usd_to_inr() if currency == "USD" else 1
                    current_value_inr = current_value * conversion_rate
                    total_cost_inr = total_cost * conversion_rate
                    profit_loss_inr = profit_loss * conversion_rate

                    # Format profit/loss string in original currency
                    if currency == "USD":
                        profit_loss_str = f"[bold red]{profit_loss:.2f}[/]" if profit_loss < 0 else f"[bold green]{profit_loss:.2f}[/]"
                    else:
                        profit_loss_str = f"[bold red]{profit_loss:.2f}[/]" if profit_loss < 0 else f"[bold green]{profit_loss:.2f}[/]"

                    if investment_type == "Stock":
                        total_stock_value += current_value_inr
                        total_invested_stock += total_cost_inr
                        stock_table.add_row(
                            str(stock_id), symbol, display_name, sector, industry, purchase_date,
                            f"{purchase_price:.2f}", str(units), currency,
                            f"{live_price:.2f} {indicator}" if live_price else "N/A",
                            profit_loss_str,
                            f"[{'bold green' if profit_loss >= 0 else 'bold red'}]{((current_value - total_cost) / total_cost * 100):.2f}%[/]" if live_price else "N/A"
                        )
                    else:
                        total_fund_value += current_value_inr
                        total_invested_fund += total_cost_inr
                        fund_table.add_row(
                            str(stock_id), symbol, display_name, "N/A", "N/A", purchase_date,
                            f"{purchase_price:.2f}", str(units), currency,
                            f"{live_price:.2f}" if live_price else "N/A",
                            profit_loss_str,
                            f"[{'bold green' if profit_loss >= 0 else 'bold red'}]{((current_value - total_cost) / total_cost * 100):.2f}%[/]" if live_price else "N/A"
                        )

                # Print Stock Table
                if len(stock_table.rows) > 0:
                    console.print(stock_table)
                    difference_stock = total_stock_value - total_invested_stock
                    difference_stock_str = f"[bold red]{difference_stock:.2f}[/]" if difference_stock < 0 else f"[bold green]{difference_stock:.2f}[/]"
                    console.print(f"💰 [bold cyan]Total Invested in Stocks: ₹{total_invested_stock:.2f}[/]")
                    console.print(f"💰 [bold cyan]Difference in Stocks: ₹{difference_stock_str}[/]\n")

                # Print Mutual Fund Table
                if len(fund_table.rows) > 0:
                    console.print(fund_table)
                    difference_fund = total_fund_value - total_invested_fund
                    difference_fund_str = f"[bold red]{difference_fund:.2f}[/]" if difference_fund < 0 else f"[bold green]{difference_fund:.2f}[/]"
                    console.print(f"💰 [bold magenta]Total Invested in Mutual Funds: ₹{total_invested_fund:.2f}[/]")
                    console.print(f"💰 [bold magenta]Difference in Mutual Funds: ₹{difference_fund_str}[/]\n")

                # Print Total Portfolio Summary
                total_portfolio_value = total_stock_value + total_fund_value
                total_portfolio_invested = total_invested_stock + total_invested_fund
                total_portfolio_difference = total_portfolio_value - total_portfolio_invested
                total_portfolio_difference_str = f"[bold red]{total_portfolio_difference:.2f}[/]" if total_portfolio_difference < 0 else f"[bold green]{total_portfolio_difference:.2f}[/]"

                console.print(f"💰 [bold cyan]Total Portfolio Invested Amount: ₹{total_portfolio_invested:.2f}[/]")
                console.print(f"💰 [bold cyan]Total Portfolio Value: ₹{total_portfolio_value:.2f}[/]")
                console.print(f"💰 [bold cyan]Total Portfolio Difference: ₹{total_portfolio_difference_str}[/]")

        elif choice == "3":
            try:
                stock_id = int(input("Enter Stock ID to Delete: ").strip())
                delete_investment()
            except ValueError:
                console.print("[bold red]❌ Invalid Stock ID! Please enter a number.[/]")
                continue

        elif choice == "4":
            console.print("[bold green]👋 Exiting... Have a great day![/]")
            break

        elif choice == "5":
            stock = input("Enter Stock Symbol (e.g., AAPL, RELIANCE.NS): ").strip().upper()
            
            # Let the user choose a time period
            console.print("\n[bold]Select Time Period:[/]")
            console.print("1. [bold]1 Month[/]")
            console.print("2. [bold]6 Months[/]")
            console.print("3. [bold]1 Year[/]")
            period_choice = input("Enter your choice (1-3): ").strip()

            # Map selection to period strings
            period_mapping = {"1": "1mo", "2": "6mo", "3": "1y"}
            period = period_mapping.get(period_choice, "1mo")  # Default to 1 month

            # Fetch historical data
            history = get_historical_price(stock, period)

            if history is not None:
                console.print(f"\n[bold cyan]📊 Historical Closing Prices for {stock} ({period}):[/]")
                console.print(history.to_string())  # Display full series
            else:
                console.print("[bold red]⚠️ No historical data found.[/]")

        elif choice == "6":
            from database import update_price_history
            update_price_history()
            print("✅ Prices updated successfully!")
            
        elif choice == "7":
            from database import get_portfolio_insights
            allocations, warnings, geographic_allocation = get_portfolio_insights()
            
            if allocations:
                # Display Geographic Exposure
                console.print("\n[bold cyan]🌍 Geographic Exposure[/]")
                geo_table = Table(title="Geographic Allocation", title_style="bold cyan")
                geo_table.add_column("Region", style="bold white")
                geo_table.add_column("Value (₹)", justify="right", style="green")
                geo_table.add_column("Allocation %", justify="right", style="cyan")
                
                for currency, value, percentage in geographic_allocation:
                    region = "Indian Market (INR)" if currency == "INR" else "US Market (USD)"
                    geo_table.add_row(
                        region,
                        f"₹{value:,.2f}",
                        f"{percentage:.2f}%"
                    )
                
                console.print(geo_table)
                console.print()

                # Display Industry Allocation
                console.print("[bold cyan]📊 Industry Allocation[/]")
                table = Table(title="Industry Allocation", title_style="bold cyan")
                table.add_column("Industry", style="bold white")
                table.add_column("Value (₹)", justify="right", style="green")
                table.add_column("Allocation %", justify="right", style="cyan")
                table.add_column("Risk Level", style="bold red")
                
                for industry, value, percentage, risk_level in allocations:
                    table.add_row(
                        industry,
                        f"₹{value:,.2f}",
                        f"{percentage:.2f}%",
                        risk_level
                    )
                
                # Display any risk warnings
                if warnings:
                    console.print("\n[bold red]Risk Warnings:[/]")
                    for warning in warnings:
                        console.print(warning)
                
                console.print(table)
            else:
                console.print("[bold red]No stock investments found in portfolio.[/]")
                
        elif choice == "8":
            from database import view_historical_performance
            history = view_historical_performance()
            
            if history:
                console.print("\n[bold cyan]📈 Portfolio Performance History[/]")
                table = Table(title="Last 30 Days", title_style="bold cyan")
                table.add_column("Date", style="bold white")
                table.add_column("Total Value", justify="right", style="green")
                table.add_column("Total Cost", justify="right", style="yellow")
                table.add_column("Profit/Loss", justify="right", style="bold red")
                table.add_column("INR Exposure", justify="right", style="cyan")
                table.add_column("USD Exposure", justify="right", style="magenta")
                
                for date, value, cost, pl, inr_exp, usd_exp in history:
                    pl_style = "[bold red]" if pl < 0 else "[bold green]"
                    table.add_row(
                        date,
                        f"₹{value:,.2f}",
                        f"₹{cost:,.2f}",
                        f"{pl_style}₹{pl:,.2f}[/]",
                        f"₹{inr_exp:,.2f}",
                        f"₹{usd_exp:,.2f}"
                    )
                
                console.print(table)
            else:
                console.print("[bold red]No historical data available yet.[/]")
                

if __name__ == "__main__":
    main()
