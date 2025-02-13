from database import (
    initialize_db, add_investment, view_portfolio, delete_stock,
    get_live_price, get_mutual_fund_nav, get_usd_to_inr, get_historical_price
)
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
        console.print("3. [bold]Delete Stock[/]")
        console.print("4. [bold]Exit[/]")
        console.print("5. [bold]View Historical Stock Performance[/]")

        choice = input("Enter your choice (1-5): ").strip()

        if choice not in ["1", "2", "3", "4", "5"]:
            console.print("[bold red]❌ Invalid choice! Please enter a number between 1 and 5.[/]")
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
                currency = "INR" if investment_type == "Mutual Fund" or symbol.endswith(".NS") else "USD"

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
                    table.add_column("Purchase Date", justify="center", style="bold white")
                    table.add_column("Buy Price", justify="right", style="green")
                    table.add_column("Units", justify="center", style="cyan")
                    table.add_column("Currency", justify="center", style="magenta")
                    table.add_column("Current Price/NAV", justify="right", style="bold green")
                    table.add_column("Profit/Loss", justify="right", style="bold red")

                total_stock_value = 0
                total_fund_value = 0
                total_invested_stock = 0
                total_invested_fund = 0

                for record in records:
                    stock_id, investment_type, symbol, name, purchase_date, purchase_price, units, currency = record

                    # Ensure name is correctly displayed
                    display_name = symbol  # Use symbol as display name

                    # Ensure name is correctly displayed
                    display_name = name if name and name != symbol else "Unknown"  # Prevents symbol duplication

                    # Fetch the latest price
                    if investment_type == "Stock":
                        live_price = get_live_price(symbol, currency)
                    else:
                        live_price = get_mutual_fund_nav(symbol)

                    if purchase_price is None:
                        console.print(f"[bold red]⚠️ Purchase price for {symbol} is not available.[/]")
                        continue

                    total_cost = purchase_price * units
                    current_value = (live_price * units) if live_price else 0
                    profit_loss = (current_value - total_cost) if live_price else 0

                    if currency == "USD":
                        conversion_rate = get_usd_to_inr()
                        current_value_inr = current_value * conversion_rate if current_value else 0
                        total_cost_inr = total_cost * conversion_rate
                    else:
                        current_value_inr = current_value
                        total_cost_inr = total_cost

                    profit_loss_str = f"[bold red]{profit_loss:.2f}[/]" if profit_loss < 0 else f"[bold green]{profit_loss:.2f}[/]"

                    if investment_type == "Stock":
                        total_stock_value += current_value_inr
                        total_invested_stock += total_cost_inr
                        stock_table.add_row(
                            str(stock_id), symbol, display_name, purchase_date,
                            f"{purchase_price:.2f}", str(units), currency,
                            f"{live_price:.2f}" if live_price else "N/A",
                            profit_loss_str
                        )
                    else:
                        total_fund_value += current_value_inr
                        total_invested_fund += total_cost_inr
                        fund_table.add_row(
                            str(stock_id), symbol, display_name, purchase_date,
                            f"{purchase_price:.2f}", str(units), currency,
                            f"{live_price:.2f}" if live_price else "N/A",
                            profit_loss_str
                        )

                # Print Stock Table
                if len(stock_table.rows) > 0:
                    console.print(stock_table)
                    difference_stock = total_stock_value - total_invested_stock
                    difference_stock_str = f"[bold red]{difference_stock:.2f}[/]" if difference_stock < 0 else f"[bold green]{difference_stock:.2f}[/]"
                    console.print(f"💰 [bold cyan]Total Invested in Stocks (INR): {total_invested_stock:.2f}[/]")
                    console.print(f"💰 [bold cyan]Difference in Stocks (INR): {difference_stock_str}[/]\n")

                # Print Mutual Fund Table
                    console.print(stock_table)

                if len(fund_table.rows) > 0:
                console.print(fund_table)
                    difference_fund = total_fund_value - total_invested_fund
                    difference_fund_str = f"[bold red]{difference_fund:.2f}[/]" if difference_fund < 0 else f"[bold green]{difference_fund:.2f}[/]"
                    console.print(f"💰 [bold magenta]Total Invested in Mutual Funds (INR): {total_invested_fund:.2f}[/]")
                    console.print(f"💰 [bold magenta]Difference in Mutual Funds (INR): {difference_fund_str}[/]\n")

                # Print Total Portfolio Summary
                total_portfolio_value = total_stock_value + total_fund_value
                total_portfolio_invested = total_invested_stock + total_invested_fund
                total_portfolio_difference = total_portfolio_value - total_portfolio_invested
                total_portfolio_difference_str = f"[bold red]{total_portfolio_difference:.2f}[/]" if total_portfolio_difference < 0 else f"[bold green]{total_portfolio_difference:.2f}[/]"

                console.print(f"💰 [bold cyan]Total Portfolio Invested Amount (INR): {total_portfolio_invested:.2f}[/]")
                console.print(f"💰 [bold cyan]Total Portfolio Value (INR): {total_portfolio_value:.2f}[/]")
                console.print(f"💰 [bold cyan]Total Portfolio Difference (INR): {total_portfolio_difference_str}[/]")
                    console.print(fund_table)

        elif choice == "3":
            try:
                stock_id = int(input("Enter Stock ID to Delete: ").strip())
                delete_stock(stock_id)
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

if __name__ == "__main__":
    main()
