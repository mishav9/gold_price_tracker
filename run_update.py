from price_checker import GoldPriceTrackerFixed

def run_single_update():
    print("Starting single price update...")
    tracker = GoldPriceTrackerFixed()
    price = tracker.update_price()
    if price:
        print(f"Successfully updated price: {price}")
    else:
        print("Failed to update price")

if __name__ == "__main__":
    run_single_update()
