# app/main.py
import requests
import time
import pickle
import numpy as np
import pandas as pd
from collections import defaultdict
from fastapi import FastAPI, Request, Response

# loading model and configuration
MODEL_PATH = "model.pkl"

try:
    with open(MODEL_PATH, 'rb') as file:
        model = pickle.load(file)
    print("Model loaded successfully")

except FileNotFoundError:
    print(f"Error: Model file not found at {MODEL_PATH}. Gateway will not use AI.")
    model = None

# in-memory stores for real-time feature calculation
IP_TIMESTAMPS = defaultdict(list)
IP_ERROR_COUNT = defaultdict(int)
IP_PATH_TRACKER = defaultdict(set)
TIMEFRAME = 60 # seconds

# for analytics
total_requests_processed = 0
total_requests_blocked = 0


# # Configure for rate limiting
# RATE_LIMIT_THRESHOLD = 20
# RATE_LIMIT_TIMEFRAME = 60 #seconds

# # this dict will store request timestamps for each IP
# request_logs = defaultdict(list)

# the service to protect. From Docker's network
TARGET_SERVICE_URL = "http://mock-backend:5000"

app = FastAPI(title="PathHelm Gateway")

@app.get("/pathhelm/status", tags=["PathHelm Internals"])
async def get_status():
    """Returns the current status and analytics of the gateway"""
    return {
        "total_requests_processed": total_requests_processed,
        "total_requests_blocked": total_requests_blocked,
        "currently_tracking_ips": len(IP_TIMESTAMPS) 
    }

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(request: Request, path: str):
    """
    captures all incoming requests and forwards 
    them to the target service
    """

    global total_requests_processed, total_requests_blocked
    total_requests_processed += 1
    # rate limiter logic
    client_ip = request.client.host
    current_time = time.time()

    # # clear old timestamps outside our timeframe
    # request_logs[client_ip] = [t for t in request_logs[client_ip] if current_time - t < RATE_LIMIT_TIMEFRAME]

    # # check if the number of recent requests exceeds the threshold
    # if len(request_logs[client_ip]) >= RATE_LIMIT_THRESHOLD:
    #     return Response(content="Too many request", status_code=429)

    # # log the current request timestamp
    # request_logs[client_ip].append(current_time)

    # Feature Calculation
    
    # clear out old data
    IP_TIMESTAMPS[client_ip] = [t for t in IP_TIMESTAMPS[client_ip] if current_time - t < TIMEFRAME]
    # calculate features for the current request
    request_frequency = len(IP_TIMESTAMPS[client_ip])
    # to prevent xero division if there are no requests
    error_rate = (IP_ERROR_COUNT.get(client_ip, 0) / request_frequency) if request_frequency > 0 else 0
    unique_paths = len(IP_PATH_TRACKER.get(client_ip, set()))

    # AI prediction
    if model:
        # create a dataframe with the feature names
        live_features = pd.DataFrame(
            [[request_frequency, error_rate, unique_paths]],
            columns=['request_frequency', 'error_rate', 'unique_paths_accessed']
        )
        prediction = model.predict(live_features)


        if prediction[0] == -1: # anomaly
            total_requests_blocked += 1
            print(f"ANOMALY DETECTED from IP: {client_ip}. Features: {live_features.values}. Blocking request.")
            return Response(content="Forbidden: Malicious activity suspected", status_code=403)
    try:
        # Forward request to targetting service
        response = requests.request(
            method=request.method,
            url=f"{TARGET_SERVICE_URL}/{path}",
            # Pass along query headers, query params, and body
            headers={k: v for k, v in request.headers.items() if k.lower() != 'host'},
            params=request.query_params,
            data=await request.body(),
            stream=True # Essential for handling file uploads or large responses
        )

        # update trackers post request
            # if backend returned an error, increment the error count for this IP
        if response.status_code >= 400:
            IP_ERROR_COUNT[client_ip] += 1

        # return the response from the target service back to the client
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    finally:
        # update trackers regardless of success or failure
        IP_TIMESTAMPS[client_ip].append(current_time)
        IP_PATH_TRACKER[client_ip].add(path)