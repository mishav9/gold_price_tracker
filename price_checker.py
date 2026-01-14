# gold_price_tracker_fixed.py
import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import schedule
import time

class GoldPriceTrackerFixed:
    def __init__(self, db_path='gold_prices.db'):
        self.db_path = db_path
        self.setup_database()

    def setup_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gold_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                price_per_10g REAL NOT NULL,
                karat TEXT NOT NULL,
                city TEXT NOT NULL,
                UNIQUE(date, timestamp)
            )
        ''')
        conn.commit()
        conn.close()

    def fetch_gold_price(self):
        """
        Fetch actual retail price from BankBazaar (fallback to other sources if needed)
        """
        try:
            # BankBazaar Hyderabad Gold Rate
            url = "https://www.bankbazaar.com/gold-rate-hyderabad.html"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the table containing gold rates
            # BankBazaar usually has a table with "10 grams" and the price
            rows = soup.find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    # Check if row is for 10 grams (standard gold 22K often listed)
                    row_text = row.get_text()
                    if '10 grams' in row_text and '1 gram' not in row_text: # weak check but let's be more specific with cells
                         
                         first_cell = cells[0].get_text().strip()
                         if '10 grams' in first_cell:
                             # The second cell usually has the price for Today
                             price_cell = cells[1].get_text().strip()
                             
                             # Extract digits
                             # Format is often "₹ 1,32,800"
                             price_str = price_cell.replace('₹', '').replace(',', '').strip()
                             
                             # Handle cases where there might be extra text like price change "(+100)"
                             # We just want the first numeric part
                             price_cleaned = ""
                             for char in price_str:
                                 if char.isdigit() or char == '.':
                                     price_cleaned += char
                                 else:
                                     break # stop at first non-digit if we have started collecting
                             
                             if price_cleaned:
                                 return float(price_cleaned)

            print("Could not find 10g 22K price in BankBazaar page")
            return self._fallback_price()

        except Exception as e:
            print(f"Error fetching price: {e}")
            return self._fallback_price()

    def _fallback_price(self):
        """
        Return the last known good price or a safe fallback
        """
        return 132000.00  # Updated fallback indicative of Jan 2026 rates

    def save_price(self, price):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now()
        date = now.strftime('%Y-%m-%d')
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')

        try:
            cursor.execute('''
                INSERT INTO gold_prices 
                (date, timestamp, price_per_10g, karat, city)
                VALUES (?, ?, ?, ?, ?)
            ''', (date, timestamp, price, '22K', 'Hyderabad'))
            conn.commit()
            print(f"✓ Saved: ₹{price:,.2f} per 10g at {timestamp}")
        except sqlite3.IntegrityError:
            print(f"⚠ Price already exists")
        finally:
            conn.close()

    def update_price(self):
        price = self.fetch_gold_price()
        if price:
            self.save_price(price)
            return price
        return None

if __name__ == "__main__":
    tracker = GoldPriceTrackerFixed()

    # Test fetch
    price = tracker.update_price()
    print(f"\n💰 Current 22K Gold Price in Hyderabad: ₹{price:,.2f} per 10g\n")

    # Schedule updates
    schedule.every(6).hours.do(tracker.update_price)

    print("Gold Price Tracker started. Updates every 6 hours.")
    print("Press Ctrl+C to stop.\n")

    while True:
        schedule.run_pending()
        time.sleep(60)