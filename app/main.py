# app/main.py
import os
import requests
import time
import pickle
import numpy as np
import pandas as pd
import redis
# from collections import defaultdict
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


TARGET_SERVICE_URL = os.getenv("TARGET_SERVICE_URL", "http://mock-backend:5000")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
# Global states and constants
TIMEFRAME = 60 # seconds

# redis connection
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    r.ping()
    print(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}.")
except redis.exceptions.ConnectionError as e:
    print(f"Could not connect to Redis: {e}. AI features will be disabled.")
    r = None


app = FastAPI(title="PathHelm Gateway")

@app.get("/pathhelm/status", tags=["PathHelm Internals"])
async def get_status():
    """Returns the current status and analytics of the gateway"""
    
    # fetch counters from Redis.. if they don't exist, default to 0.
    total_processed = int(r.get("analytics:total_requests") or 0)
    total_blocked = int(r.get("analytics:total_requests_blocked") or 0)
    
    active_ips = r.keys("*:timestamps") if r else []
    return {
        "total_requests_processed": total_processed,
        "total_requests_blocked": total_blocked,
        "currently_tracking_ips": len(active_ips) 
    }

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(request: Request, path: str):
    """
    captures all incoming requests and forwards 
    them to the target service
    """
    if r:
        # Increment the total requests counter in Redis
        r.incr("analytics:total_requests")
        
    # rate limiter logic
    client_ip = request.client.host

# AI prediction logic using redis
    if r and model:
        current_time = time.time()

        # defining unique keys for this IP in Redis
        timestamps_key = f"{client_ip}:timestamps"
        error_count_key = f"{client_ip}:errors"
        paths_key = f"{client_ip}:paths"

        # Feature Calculation
        
        # 1. Request Frequency
        # first, remove timestamps that are older than our timeframe
        min_time = current_time - TIMEFRAME
        r.zremrangebyscore(timestamps_key, '-inf', min_time)
        request_frequency = r.zcard(timestamps_key)

        # 2. Error rate
        error_count = int(r.get(error_count_key) or 0)
        error_rate = (error_count / request_frequency) if request_frequency > 1 else 0

        # 3. unique paths accessed
        unique_paths = r.scard(paths_key)

        live_features = pd.DataFrame(
            [[request_frequency, error_rate, unique_paths]],
            columns=['request_frequency', 'error_rate', 'unique_paths_accessed']
        )
        prediction = model.predict(live_features)


        if prediction[0] == -1: # anomaly
            if r:
                # Increment the blocked requests counter in Redis
                r.incr("analytics:total_requests_blocked")
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

        # update in redis post request
        if r:
            # if backend returned an error, increment the error count for this IP
            if response.status_code >= 400:
                r.incr(error_count_key)
                r.expire(error_count_key, TIMEFRAME) #reset counter after timeframe
            
            # add current request timestamp to a sorted set
            r.zadd(timestamps_key, {str(time.time()): time.time()})
            r.expire(timestamps_key, TIMEFRAME)

            # add the accessed path to a set for this ip
            r.sadd(paths_key, path)
            r.expire(paths_key, TIMEFRAME)

        # return the response from the target service back to the client
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except requests.exceptions.RequestException as e:
        return Response(content=f"An error occurred while proxying: {e}", status_code=502)