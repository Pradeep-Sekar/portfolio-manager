import sqlite3
import yfinance as yf

def update_existing_stocks():
    """Fetch and update sector/industry info for stocks missing them."""
    conn = sqlite3.connect("portfolio.db")
    cursor = conn.cursor()

    # Fetch all stocks that need sector info
    cursor.execute("SELECT id, symbol FROM portfolio WHERE sector IS NULL OR sector = 'N/A'")
    stocks_to_update = cursor.fetchall()

    if not stocks_to_update:
        print("✅ All stocks already have sector information!")
        return

    print(f"🔄 Updating {len(stocks_to_update)} stocks with missing sector info...")

    for stock_id, symbol in stocks_to_update:
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            sector = info.get("sector", "N/A")
            industry = info.get("industry", "N/A")

            if sector != "N/A":  # Only update if data is found
                cursor.execute("""
                    UPDATE portfolio SET sector = ?, industry = ? WHERE id = ?
                """, (sector, industry, stock_id))
                print(f"✅ Updated {symbol} → Sector: {sector}, Industry: {industry}")
            else:
                print(f"⚠️ No sector data found for {symbol}")

        except Exception as e:
            print(f"❌ Error updating {symbol}: {e}")

    conn.commit()
    conn.close()
    print("✅ Sector info update completed!")

# Run the update function
update_existing_stocks()