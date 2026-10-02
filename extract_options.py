import os
import json
import psycopg
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()
DB_URI = os.getenv("DB_URI")

def fetch_free_market_data():
    """Fetches real end-of-day data for Nifty 50 and Reliance using Yahoo Finance."""
    print("Fetching free market data from Yahoo Finance...")
    
    # ^NSEI is the ticker for Nifty 50 Index
    nifty = yf.Ticker("^NSEI")
    reliance = yf.Ticker("RELIANCE.NS")
    
    # Get today's market data
    nifty_data = nifty.history(period="1d")
    reliance_data = reliance.history(period="1d")
    
    # Package it into a JSON format just like a REST API would
    payload = {
        "status": "success",
        "source": "yfinance",
        "date": nifty_data.index[0].strftime('%Y-%m-%d'),
        "assets": [
            {
                "symbol": "NIFTY_50",
                "open": round(nifty_data['Open'].iloc[0], 2),
                "close": round(nifty_data['Close'].iloc[0], 2),
                "volume": int(nifty_data['Volume'].iloc[0])
            },
            {
                "symbol": "RELIANCE",
                "open": round(reliance_data['Open'].iloc[0], 2),
                "close": round(reliance_data['Close'].iloc[0], 2),
                "volume": int(reliance_data['Volume'].iloc[0])
            }
        ]
    }
    return payload

def load_to_bronze(raw_data: dict):
    print("Connecting to PostgreSQL to load data...")
    with psycopg.connect(DB_URI) as conn:
        with conn.cursor() as cur:
            json_payload = json.dumps(raw_data)
            cur.execute("""
                INSERT INTO bronze_raw_options (raw_payload)
                VALUES (%s);
            """, (json_payload,))
            print("Successfully inserted free market data into Postgres!")

if __name__ == "__main__":
    data = fetch_free_market_data()
    load_to_bronze(data)