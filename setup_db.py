import os
import psycopg
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

# Get the database URI we set in the .env file
DB_URI = os.getenv("DB_URI")

def setup_database():
    # Connect to the database
    with psycopg.connect(DB_URI) as conn:
        with conn.cursor() as cur:
            print("Connected to PostgreSQL successfully.")
            
            # Create the bronze table for raw JSON ingestion
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bronze_raw_options (
                    id SERIAL PRIMARY KEY,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    raw_payload JSONB NOT NULL
                );
            """)
            print("Table 'bronze_raw_options' created.")

if __name__ == "__main__":
    setup_database()