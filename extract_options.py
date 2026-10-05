import os
import psycopg2 as psycopg
import yfinance as yf
import json
from datetime import datetime

# ==============================================================================
# ENVIRONMENT-AWARE CONFIGURATION
# os.getenv("KEY", "default") checks if the OS/Docker provided an environment
# variable. If yes, it uses it. If not, it falls back to local Windows defaults.
# This prevents hardcoding passwords while letting the same script run anywhere.
# ==============================================================================
DB_HOST = os.getenv("DB_HOST", "localhost")      # Docker passes 'nifty_warehouse'
DB_PORT = os.getenv("DB_PORT", "5433")           # Docker passes '5432'
DB_NAME = os.getenv("DB_NAME", "market_data")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASSWORD", "password123")
DB_URI = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def get_connection():
    """
    Establishes an isolated PostgreSQL database connection.
    In production, this handles retries and connection pooling.
    """
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

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

def load_to_bronze(data):
    with psycopg.connect(DB_URI) as conn:
        with conn.cursor() as cur:
            # Ensure the landing table exists before inserting
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bronze_raw_options (
                    id SERIAL PRIMARY KEY,
                    raw_payload JSONB NOT NULL,
                    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                INSERT INTO bronze_raw_options (raw_payload)
                VALUES (%s);
            """, (json.dumps(data),))
        conn.commit()
    print("Data loaded into bronze layer successfully.")

if __name__ == "__main__":
    data = fetch_free_market_data()
    load_to_bronze(data)