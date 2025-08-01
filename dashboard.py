# dashboard.py

import streamlit as st
import requests
import time
import pandas as pd
import os
import sqlite3 # Make sure this is imported
from datetime import datetime, timedelta

# page Configuration
st.set_page_config(
    page_title="PathHelm",
    page_icon="🛡️",
    layout="wide"
)

# app title
st.title("🛡️ PathHelm Live Analytics")

# fetching data
PATHHELM_STATUS_URL = "http://pathhelm:8000/pathhelm/status"
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
HEADERS = {"X-Admin-Api-Key": ADMIN_API_KEY} if ADMIN_API_KEY else {}

# sqlite path for dashboard
# MODIFIED: Ensure this path matches the volume mount in docker-compose.yml
DB_FILE = "/code/history-data/pathhelm_history.db" 

st.header("Live Traffic Overview")
live_placeholder = st.empty() # This will hold the live metrics and chart

st.header("Historical Traffic Analysis")

# date range for historical data
col1, col2 = st.columns(2)
with col1:
    end_date = st.date_input("End Date", datetime.now().date())
with col2:
    # default to last 7 days
    start_date = st.date_input("Start Date", end_date - timedelta(days=7)) 

# case: start date is not after end date
if start_date > end_date:
    st.error("Error: Start date cannot be after end date.")
    start_date = end_date

@st.cache_data(ttl=60) # cache data for 60 seconds
def get_historical_data(start_dt: datetime, end_dt: datetime): # Added type hints for clarity
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        query = f"""
            SELECT
                timestamp,
                total_requests_processed,
                total_requests_blocked,
                currently_tracking_ips
            FROM
                analytics_history
            WHERE timestamp BETWEEN '{start_dt.isoformat()}' AND '{end_dt.isoformat()}'
            ORDER BY timestamp ASC
            """
        historical_df = pd.read_sql_query(query, conn)
        historical_df['timestamp'] = pd.to_datetime(historical_df["timestamp"]) # Fixed typo: pd.to.datetime -> pd.to_datetime
        historical_df.set_index('timestamp', inplace=True)
        return historical_df
    except sqlite3.Error as e:
        st.error(f"Database error: {e}. Ensure history collector is running and {DB_FILE} exists.")
        return pd.DataFrame() # empty DataFrame on error
    finally:
        if conn:
            conn.close()

# Corrected call to get_historical_data
# Combine date objects with min/max time to create datetime objects for the query
historical_df = get_historical_data(
    datetime.combine(start_date, datetime.min.time()),
    datetime.combine(end_date, datetime.max.time())
)

if not historical_df.empty:
    st.subheader("Historical Trends")
    # Ensure columns exist before plotting
    if 'total_requests_processed' in historical_df.columns and 'total_requests_blocked' in historical_df.columns:
        st.line_chart(historical_df[['total_requests_processed', 'total_requests_blocked']])
    else:
        st.warning("Historical data columns 'total_requests_processed' or 'total_requests_blocked' not found.")

    st.subheader("Historical Data Table")
    st.dataframe(historical_df)
else:
    st.info("No historical data available for the selected date range. Ensure the history collector is running and collecting data.")

    
def get_stats():
    """fetches stats from the PathHelm status endpoint."""
    try:
        response = requests.get(PATHHELM_STATUS_URL, headers=HEADERS, timeout=2)
        response.raise_for_status()  # exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        # More informative error message for the live section
        st.error(f"Error connecting to PathHelm API for live data: {e}. Ensure PathHelm is running, ADMIN_API_KEY is correct, and the gateway's status endpoint is accessible.")
        return None

# live update loop
while True:
    stats = get_stats()

    if stats:
        with live_placeholder.container(): # Use live_placeholder consistently
            # three columns for the metrics
            kpi1, kpi2, kpi3 = st.columns(3)

            kpi1.metric(
                label="Total Requests Processed 📦",
                value=f"{stats.get('total_requests_processed', 0):,}"
            )
            kpi2.metric( # Removed delta for simplicity, as it requires tracking previous state
                label="Total Requests Blocked 🚫",
                value=f"{stats.get('total_requests_blocked', 0):,}"
            )
            kpi3.metric(
                label="Currently Tracking IPs 📍",
                value=stats.get('currently_tracking_ips', 0)
            )

            # create a simple chart
            st.subheader("Blocked vs. Processed Requests")
            processed = stats.get('total_requests_processed', 0)
            blocked = stats.get('total_requests_blocked', 0)
            allowed = processed - blocked

            chart_data = pd.DataFrame({
                "Category": ["Allowed", "Blocked"],
                "Count": [allowed, blocked]
            })
            
            st.bar_chart(chart_data, x="Category", y="Count")

    # No else block here for the live_placeholder, as the error message is already handled in get_stats
    # and displayed directly by st.error.

    time.sleep(2) # refresh every 2 seconds