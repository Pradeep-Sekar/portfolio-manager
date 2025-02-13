from database import initialize_db, add_stock, view_portfolio, delete_stock, get_live_price, get_usd_to_inr
from tabulate import tabulate

def main():
    initialize_db()
    while True:
        print("\n📊 Stock Portfolio Manager")
        print("1. Add Stock")
        print("2. View Portfolio (with Profit/Loss)")
        print("3. Delete Stock")
        print("4. Exit")
        print("5. View Historical Stock Performance")

        choice = input("Enter your choice (1-4): ").strip()

        if choice not in ["1", "2", "3", "4"]:
            print("❌ Invalid choice! Please enter a number between 1 and 4.")
            continue

        if choice == "1":
            while True:  # Loop until a valid stock is entered
                stock = input("Enter Stock Symbol (e.g., AAPL, RELIANCE.NS): ").strip().upper()
                purchase_date = input("Enter Purchase Date (YYYY-MM-DD): ").strip()

                try:
                    purchase_price = float(input("Enter Purchase Price: ").strip())
                    units = int(input("Enter Number of Units: ").strip())
                except ValueError:
                    print("❌ Invalid input! Price must be a number, and units must be an integer.")
                    continue

                # Determine currency
                currency = "INR" if stock.endswith(".NS") else "USD"

                # Validate stock by checking if a price exists
                if get_live_price(stock, currency) is None:
                    print(f"❌ {stock} is not a valid stock symbol. Please enter a correct ticker.")
                    continue  # Ask for input again

                # If stock is valid, add it to the database
                add_stock(stock, purchase_date, purchase_price, units, currency)
                break  # Exit loop
        elif choice == "2":  # View portfolio with profit/loss
            records = view_portfolio()
            if records:
                table_data = []
                total_value_inr = 0
                for record in records:
                    stock_id, stock_symbol, purchase_date, purchase_price, units, *rest = record
                    currency = "INR" if stock_symbol.endswith(".NS") else "USD"
                    live_price = get_live_price(stock_symbol, currency)
                    total_cost = purchase_price * units
                    current_value = (live_price * units) if live_price else None
                    profit_loss = (current_value - total_cost) if live_price else None
                    
                    # Convert current value to INR if needed
                    if currency == "USD":
                        current_value_inr = current_value * get_usd_to_inr() if current_value else 0
                    else:
                        current_value_inr = current_value if current_value else 0

                    total_value_inr += current_value_inr

                    table_data.append([
                        stock_id, stock_symbol, purchase_date, purchase_price, units, currency,
                        live_price if live_price else "N/A",
                        round(profit_loss, 2) if profit_loss else "N/A"
                    ])

                print(tabulate(table_data, headers=[
                    "ID", "Stock", "Purchase Date", "Buy Price", "Units", "Currency", "Current Price", "Profit/Loss"
                ], tablefmt="grid"))
                print(f"\n💰 Total Portfolio Value (in INR): {round(total_value_inr, 2)}")
            else:
                print("📭 No records found.")

        elif choice == "3":
            try:
                stock_id = int(input("Enter Stock ID to Delete: ").strip())
                delete_stock(stock_id)
            except ValueError:
                print("❌ Invalid Stock ID! Please enter a number.")
                continue

        elif choice == "4":
            print("👋 Exiting... Have a great day!")
            break

        elif choice == "5":
            stock = input("Enter Stock Symbol (e.g., AAPL, RELIANCE.NS): ").strip().upper()
            
            # Let the user choose a time period
            print("\nSelect Time Period:")
            print("1. 1 Month")
            print("2. 6 Months")
            print("3. 1 Year")
            period_choice = input("Enter your choice (1-3): ").strip()

            # Map selection to period strings
            period_mapping = {"1": "1mo", "2": "6mo", "3": "1y"}
            period = period_mapping.get(period_choice, "1mo")  # Default to 1 month

            # Fetch historical data
            history = get_historical_price(stock, period)

            if history is not None:
                print(f"\n📊 Historical Closing Prices for {stock} ({period}):")
                print(history.to_string())  # Display full series
            else:
                print("⚠️ No historical data found.")

if __name__ == "__main__":
    main()
