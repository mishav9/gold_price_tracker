import sqlite3
from datetime import datetime, timedelta
from price_checker import GoldPriceTrackerFixed
import shutil
import os

# Backup DB
if os.path.exists('gold_prices.db'):
    shutil.copy('gold_prices.db', 'gold_prices.db.test_bak')

try:
    tracker = GoldPriceTrackerFixed()
    conn = sqlite3.connect('gold_prices.db')
    cursor = conn.cursor()

    # Insert fake high prices for the last 3 days
    # Price 150,000 > Current ~132,000 (approx 12% drop)
    high_price = 150000.00
    for i in range(1, 4):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        timestamp = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d %H:%M:%S')
        try:
            cursor.execute('''
                INSERT INTO gold_prices (date, timestamp, price_per_10g, karat, city)
                VALUES (?, ?, ?, ?, ?)
            ''', (date, timestamp, high_price, '22K', 'Hyderabad'))
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()

    print("Inserted high historical prices.")
    
    # Run update
    print("Running update...")
    tracker.update_price()

finally:
    # Restore DB
    if os.path.exists('gold_prices.db.test_bak'):
        shutil.move('gold_prices.db.test_bak', 'gold_prices.db')
        print("\nRestored original database.")
