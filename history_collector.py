# history_collector.py

import requests
import sqlite3
import time
import os
from datetime import datetime

# config
PATHHELM_STATUS_URL = os.getenv("PATHHELM_STATUS_URL", "http://pathhelm:8000/pathhelm/status")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
COLLECTION_INTERVAL_SECONDS = int(os.getenv("COLLECTION_INTERVAL_SECONDS", 60)) # collect every 60 seconds
DB_FILE = "/code/history-data/pathhelm_history.db"

# retry mechanism for initial connection
MAX_RETRIES = 10
RETRY_DELAY_SECONDS = 5

def init_db():
    """Initializes the SQLite database and creates the table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analytics_history (
            timestamp TEXT PRIMARY KEY,
            total_requests_processed INTEGER,
            total_requests_blocked INTEGER,
            currently_tracking_ips INTEGER
        )
    ''')
    conn.commit()
    conn.close()
    print(f"SQLite database '{DB_FILE}' initialized.")

def collect_and_store_data(headers):
    """Fetches data from PathHelm and stores it in the SQLite database."""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(PATHHELM_STATUS_URL, headers=headers, timeout=5)
            response.raise_for_status()
            stats = response.json()

            timestamp = datetime.now().isoformat()
            total_processed = stats.get('total_requests_processed', 0)
            total_blocked = stats.get('total_requests_blocked', 0)
            currently_tracking_ips = stats.get('currently_tracking_ips', 0)

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO analytics_history (timestamp, total_requests_processed, total_requests_blocked, currently_tracking_ips)
                VALUES (?, ?, ?, ?)
            ''', (timestamp, total_processed, total_blocked, currently_tracking_ips))
            conn.commit()
            conn.close()
            print(f"Data collected and stored at {timestamp}: Processed={total_processed}, Blocked={total_blocked}")
            return # victory, exit retry loop
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to PathHelm status endpoint (Attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS) # wait before retrying
            else:
                print(f"Failed to connect to PathHelm status endpoint after {MAX_RETRIES} attempts. Skipping this collection cycle.")
        except Exception as e:
            print(f"An unexpected error occurred during data collection: {e}")
            return

if __name__ == "__main__":
    print("Starting PathHelm History Collector...")
    
    if not ADMIN_API_KEY:
        print("ERROR: ADMIN_API_KEY environment variable is not set. History collector cannot authenticate.")
        exit(1)

    HEADERS = {"X-Admin-Api-Key": ADMIN_API_KEY} 
    
    init_db()
    while True:
        collect_and_store_data(HEADERS)
        time.sleep(COLLECTION_INTERVAL_SECONDS)