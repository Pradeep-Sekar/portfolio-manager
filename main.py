from database import initialize_db, add_stock, view_portfolio, delete_stock, get_live_price
from tabulate import tabulate

def main():
    initialize_db()
    while True:
        print("\n📊 Stock Portfolio Manager")
        print("1. Add Stock")
        print("2. View Portfolio (with Profit/Loss)")
        print("3. Delete Stock")
        print("4. Exit")

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
                for record in records:
                    stock_id, stock_symbol, purchase_date, purchase_price, units, *rest = record
                    currency = "INR" if stock_symbol.endswith(".NS") else "USD"
                    live_price = get_live_price(stock_symbol, currency)
                    total_cost = purchase_price * units
                    current_value = (live_price * units) if live_price else None
                    profit_loss = (current_value - total_cost) if live_price else None
                    
                    table_data.append([
                        stock_id, stock_symbol, purchase_date, purchase_price, units,
                        live_price if live_price else "N/A",
                        round(profit_loss, 2) if profit_loss else "N/A"
                    ])

                print(tabulate(table_data, headers=[
                    "ID", "Stock", "Purchase Date", "Buy Price", "Units", "Current Price", "Profit/Loss"
                ], tablefmt="grid"))
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

if __name__ == "__main__":
    main()
