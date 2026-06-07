# 💰 Gold Price Tracker - Hyderabad

Automatically tracks the **22K gold price (per 10 grams) in Hyderabad, India**, stores the
history in a local SQLite database, and visualizes the trend through a Streamlit dashboard.
Price updates run automatically every 6 hours via GitHub Actions, and a drop alert is pushed
through [ntfy.sh](https://ntfy.sh) whenever the price falls meaningfully below its recent average.

## Why this exists

Retail gold prices change daily and are scattered across various jewellers and aggregator sites.
This repo keeps a continuous, timestamped record of the Hyderabad 22K rate so you can:

- See the current price and how it has moved over time.
- Track 7-day / 30-day averages and volatility.
- Get notified when the price dips, which is useful for timing a purchase.

## How it works

1. **Scraping** (`price_checker.py`) fetches the live retail rate, primarily from
   [GoodReturns](https://www.goodreturns.in/gold-rates/hyderabad.html), with
   [BankBazaar](https://www.bankbazaar.com/gold-rate-hyderabad.html) as a fallback.
2. **Storage** writes each reading (date, timestamp, price, karat, city) into `gold_prices.db`.
3. **Alerts** compare the new price against the 7-day moving average and push a notification to
   the ntfy topic `gold_price_hyderabad_avinash` if the price has dropped by 1% or more.
4. **Automation** (`.github/workflows/update_prices.yaml`) runs `run_update.py` every 6 hours,
   then commits the updated database back to the repo.
5. **Dashboard** (`app.py`) reads the database and renders current price, averages, an interactive
   trend chart, statistics, and a downloadable CSV.

## Project structure

| File | Purpose |
|------|---------|
| `price_checker.py` | Scraping, database, moving average, and notification logic (`GoldPriceTrackerFixed`). |
| `run_update.py` | Single-run entry point used by the GitHub Actions cron job. |
| `app.py` | Streamlit dashboard for viewing prices and trends. |
| `gold_prices.db` | SQLite database holding the price history. |
| `verify_notification.py` | Manual helper to test the drop-alert notification path. |
| `.github/workflows/update_prices.yaml` | Scheduled workflow that updates prices every 6 hours. |
| `.streamlit/config.toml` | Streamlit theme and server configuration. |

## Setup

This project uses [uv](https://github.com/astral-sh/uv) for dependency management
(`pyproject.toml` / `uv.lock`), with `requirements.txt` provided for the CI workflow.

```bash
# Using uv (recommended)
uv sync

# Or with pip
pip install -r requirements.txt
```

## Usage

**Run a one-off price update** (fetch latest price and save to the database):

```bash
uv run python run_update.py
```

**Launch the dashboard:**

```bash
uv run streamlit run app.py
```

Then open http://localhost:8501 in your browser.

**Run as a long-lived tracker** (updates every 6 hours, in-process scheduler):

```bash
uv run python price_checker.py
```

## Notifications

Drop alerts are published to the public ntfy topic `gold_price_hyderabad_avinash`. To receive
them, install the [ntfy app](https://ntfy.sh/) and subscribe to that topic, or open
https://ntfy.sh/gold_price_hyderabad_avinash in a browser.

## Notes

- Prices are indicative retail rates scraped from third-party sites and may differ from actual
  market or jeweller rates.
- Because the data comes from scraping, page-layout changes upstream can break a source; the
  fallback source and a last-known-good fallback price help keep the tracker running.
</content>
</invoke>
