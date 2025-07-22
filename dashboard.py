# dashboard.py
import streamlit as st
import requests
import time
import pandas as pd

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

def get_stats():
    """fetches stats from the PathHelm status endpoint."""
    try:
        response = requests.get(PATHHELM_STATUS_URL, timeout=2)
        response.raise_for_status()  # exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to PathHelm API: {e}")
        return None

# ui layout
placeholder = st.empty()

# live update loop
while True:
    stats = get_stats()

    if stats:
        with placeholder.container():
            # three columns for the metrics
            kpi1, kpi2, kpi3 = st.columns(3)

            kpi1.metric(
                label="Total Requests Processed 📦",
                value=f"{stats.get('total_requests_processed', 0):,}"
            )
            kpi2.metric(
                label="Total Requests Blocked 🚫",
                value=f"{stats.get('total_requests_blocked', 0):,}",
                delta=f"-{stats.get('total_requests_blocked', 0)} blocked",
                delta_color="inverse"
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

    else:
        st.warning("Could not retrieve stats. Is PathHelm running?")

    time.sleep(2) # refresh every 2 seconds