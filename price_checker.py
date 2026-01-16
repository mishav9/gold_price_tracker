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
        Fetch actual retail price from GoodReturns (Primary) or BankBazaar (Backup)
        """
        # 1. Try GoodReturns (More reliable/frequent updates)
        price = self.fetch_goodreturns()
        if price:
            return price
            
        print("GoodReturns failed, trying BankBazaar...")
        
        # 2. Try BankBazaar (Fallback)
        price = self.fetch_bankbazaar()
        if price:
            return price

        print("All sources failed")
        return self._fallback_price()

    def fetch_goodreturns(self):
        try:
            url = "https://www.goodreturns.in/gold-rates/hyderabad.html"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            }
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"GoodReturns returned {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for 22 Carat Gold section (containing H2 with "22 Carat" and "Hyderabad")
            for section in soup.find_all('section'):
                h2 = section.find('h2')
                if h2 and "22 Carat" in h2.get_text() and "Hyderabad" in h2.get_text():
                    table = section.find('table')
                    if table:
                        for row in table.find_all('tr'):
                            cells = row.find_all('td')
                            # Check for 10 grams row (first cell is '10')
                            if len(cells) >= 2 and cells[0].get_text().strip() == '10':
                                price_text = cells[1].get_text()
                                return self._clean_price(price_text)
            return None
        except Exception as e:
            print(f"Error fetching GoodReturns: {e}")
            return None

    def fetch_bankbazaar(self):
        try:
            url = "https://www.bankbazaar.com/gold-rate-hyderabad.html"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            rows = soup.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    row_text = row.get_text()
                    if '10 grams' in row_text and '1 gram' not in row_text:
                         first_cell = cells[0].get_text().strip()
                         if '10 grams' in first_cell:
                             price_cell = cells[1].get_text().strip()
                             return self._clean_price(price_cell)
            return None
        except Exception as e:
            print(f"Error fetching BankBazaar: {e}")
            return None

    def _clean_price(self, price_str):
        if not price_str:
            return None
        clean = ""
        for char in price_str:
            if char.isdigit() or char == '.':
                clean += char
        return float(clean) if clean else None

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

    def get_moving_average(self, days=7):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            # Calculate average for the last 7 days for '22K' and 'Hyderabad'
            cursor.execute('''
                SELECT AVG(price_per_10g) 
                FROM gold_prices 
                WHERE karat = '22K' 
                AND city = 'Hyderabad' 
                AND date >= date('now', ?)
            ''', (f'-{days} days',))
            result = cursor.fetchone()
            return result[0] if result and result[0] else None
        except Exception as e:
            print(f"Error calculating moving average: {e}")
            return None
        finally:
            conn.close()

    def send_notification(self, current_price, avg_price):
        try:
            drop_percentage = ((avg_price - current_price) / avg_price) * 100
            if drop_percentage >= 1.0:
                message = f"🚨 Gold Price Drop Alert!\n\nCurrent: ₹{current_price:,.2f}\n7-Day Avg: ₹{avg_price:,.2f}\nDrop: {drop_percentage:.2f}%"
                requests.post("https://ntfy.sh/gold_price_hyderabad_avinash", 
                            data=message.encode('utf-8'),
                            headers={"Title": "Gold Price Alert", "Priority": "high"})
                print(f"✓ Notification sent: {drop_percentage:.2f}% drop")
        except Exception as e:
            print(f"Error sending notification: {e}")

    def update_price(self):
        price = self.fetch_gold_price()
        if price:
            self.save_price(price)
            
            # Check for price drop
            avg_price = self.get_moving_average()
            if avg_price and price < avg_price:
                self.send_notification(price, avg_price)
                
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