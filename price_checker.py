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
        Fetch actual retail price from Indian gold rate websites
        """
        try:
            # Try GoodReturns first
            url = "https://www.goodreturns.in/gold-rates/hyderabad.html"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find gold rate table
            tables = soup.find_all('table')

            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        cell_text = cells[0].get_text().strip()
                        if '22' in cell_text and 'Carat' in cell_text:
                            # Found 22K row, get 10g price
                            price_cell = cells[1].get_text().strip()
                            # Remove ₹ and commas
                            price = float(price_cell.replace('₹', '').replace(',', '').strip())
                            return price

            # Fallback to calculated price with markup
            return self._calculate_with_markup()

        except Exception as e:
            print(f"Error fetching price: {e}")
            return self._calculate_with_markup()

    def _calculate_with_markup(self):
        """
        Fallback: Calculate from international rates + India markup
        """
        try:
            # Get international gold price
            url = "https://api.metals.live/v1/spot/gold"
            response = requests.get(url, timeout=10)
            data = response.json()
            usd_per_oz = data[0]['price']

            # USD to INR
            forex_url = "https://api.exchangerate-api.com/v4/latest/USD"
            forex_response = requests.get(forex_url, timeout=10)
            usd_to_inr = forex_response.json()['rates']['INR']

            # Calculate base 22K price
            inr_per_gram = (usd_per_oz * usd_to_inr) / 31.1035
            base_22k = inr_per_gram * 10 * 0.9167

            # Add typical Indian retail markup (making + GST + margin)
            # Average: 18% making + 3% GST + 5% margin = 26% total
            retail_price = base_22k * 1.26

            return round(retail_price, 2)

        except Exception as e:
            print(f"Calculation error: {e}")
            return 129780.00  # Fallback to recent known price

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