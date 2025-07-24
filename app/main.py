# app/main.py
import os
import requests
import time
import pickle
import numpy as np
import pandas as pd
import redis
# from collections import defaultdict
from fastapi import FastAPI, Request, Response, HTTPException, status

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
TIMEFRAME = 60 # seconds #For AI

# Rate limiting configuration
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", 100))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", 60))

# Admin apikey and ip list keys
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
# print(f"DEBUG: Loaded ADMIN_API_KEY from environment: '{ADMIN_API_KEY}' (Length: {len(ADMIN_API_KEY) if ADMIN_API_KEY else 'None'})")
IP_BLACKLIST_KEY = "ip_blacklist"
IP_WHITELIST_KEY = "ip_whitelist"


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
async def get_status(request: Request):
    """Returns the current status and analytics of the gateway"""
    authenticate_admin_key(request)
    # fetch counters from Redis.. if they don't exist, default to 0.
    total_processed = int(r.get("analytics:total_requests") or 0)
    total_blocked = int(r.get("analytics:total_requests_blocked") or 0)
    
    active_ips = r.keys("*:timestamps") if r else []
    return {
        "total_requests_processed": total_processed,
        "total_requests_blocked": total_blocked,
        "currently_tracking_ips": len(active_ips) 
    }

# admin endpoints for managing IP lists
def authenticate_admin_key(request: Request):
    """
    helper to authenticate admin apikey
    """
    # print(f"DEBUG: Entering authenticate_admin_key for request to {request.url}")
    if not ADMIN_API_KEY:
        # print("DEBUG: ADMIN_API_KEY is NOT configured. Raising 500.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Admin API key not configured on gateway.")
    
    admin_key_header = request.headers.get("x-admin-api-key")

    # print(f"DEBUG: Incoming X-Admin-Api-Key header: '{admin_key_header}'")
    # print(f"DEBUG: Expected ADMIN_API_KEY: '{ADMIN_API_KEY}'")

    if not admin_key_header or admin_key_header != ADMIN_API_KEY:
        # print("DEBUG: Admin authentication failed. Header missing or mismatch. Raising 401.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized: Invalid Admin API Key.")
    
    if not r:
        # print("DEBUG: Redis not connected during admin auth. Raising 500.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Redis not connected, cannot manage IP lists.")
    
    # print("DEBUG: Admin authentication successful.")
    

# BLACKLIST
@app.post("/pathhelm/admin/ip_blacklist", tags=["PathHelm Admin"])
async def add_to_blacklist(request: Request, ip: str):
    """
    Adds an IP address to the blacklist
    """
    authenticate_admin_key(request)
    
    if not r:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Redis not connected.")
    
    r.sadd(IP_BLACKLIST_KEY, ip)
    return {"message": f"IP {ip} added to blacklist."}

@app.delete("/pathhelm/admin/ip_blacklist", tags=["PathHelm Admin"])
async def remove_from_blacklist(request: Request, ip: str):
    """
    Removes an IP address from the blacklist
    """
    authenticate_admin_key(request)
    
    if not r:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Redis not connected.")
    
    r.srem(IP_BLACKLIST_KEY, ip)
    return {"message": f"IP {ip} removed from blacklist."}

@app.get("/pathhelm/admin/ip_blacklist", tags=["PathHelm Admin"])
async def get_blacklist(request: Request):
    """
    Returns the current IP blacklist
    """
    authenticate_admin_key(request)
    
    if not r:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Redis not connected.")

    return {"blacklist": list(r.smembers(IP_BLACKLIST_KEY))}

# WHITELIST
@app.post("/pathhelm/admin/ip_whitelist", tags=["PathHelm Admin"])
async def add_to_whitelist(request: Request, ip: str):
    """
    Adds an IP address to the whitelist
    """
    authenticate_admin_key(request)
    
    if not r:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Redis not connected.")
    
    r.sadd(IP_WHITELIST_KEY, ip)
    return {"message": f"IP {ip} added to whitelist."}

@app.delete("/pathhelm/admin/ip_whitelist", tags=["PathHelm Admin"])
async def remove_from_whitelist(request: Request, ip: str):
    """
    Removes an IP address from the whitelist
    """
    authenticate_admin_key(request)
    
    if not r:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Redis not connected.")
    
    r.srem(IP_WHITELIST_KEY, ip)
    return {"message": f"IP {ip} removed from whitelist."}

@app.get("/pathhelm/admin/ip_whitelist", tags=["PathHelm Admin"])
async def get_whitelist(request: Request):
    """
    Returns the current IP whitelist
    """
    authenticate_admin_key(request)
    
    if not r:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Redis not connected.")

    return {"whitelist": list(r.smembers(IP_WHITELIST_KEY))}



@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(request: Request, path: str):
    """
    captures all incoming requests and forwards 
    them to the target service
    """

    client_ip = request.client.host
    # print(f"DEBUG: Incoming request from client_ip: {client_ip}")

    # ip blacklist/whitelist logic (placed earlier for immediate effect)
    if r:
        # check blacklist first
        # print(f"DEBUG: Checking blacklist for IP: {client_ip}")
        is_blacklisted = r.sismember(IP_BLACKLIST_KEY, client_ip)
        # print(f"DEBUG: Is {client_ip} blacklisted? {is_blacklisted}")

        if is_blacklisted:
            print(f"IP {client_ip} is blacklisted. Blocking request.")
            # Onllly if u want the counter to increment for balcklisted ips, uncomment this
            # if r: # Increment blocked counter for blacklisted IPs
            #     r.incr("analytics:total_requests_blocked")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Your IP is blacklisted")
        
        # check whitelist next
        # print(f"DEBUG: Checking whitelist for IP: {client_ip}")
        is_whitelisted = r.sismember(IP_WHITELIST_KEY, client_ip)
        # print(f"DEBUG: Is {client_ip} whitelisted? {is_whitelisted}")
        if is_whitelisted:
            print(f"IP {client_ip} is whitelisted. Allowing request, bypassing other protocols.")
            # increment total requests, but bypass apikey, ratelimit and ai
            if r:
                r.incr("analytics:total_requests")
                # direct proxy
                try:
                    response = requests.request(
                        method=request.method,
                        url=f"{TARGET_SERVICE_URL}/{path}",
                        # Pass along query headers, query params, and body
                        headers={k: v for k, v in request.headers.items() if k.lower() != 'host'},
                        params=request.query_params,
                        data=await request.body(),
                        stream=True # essential for handling file uploads or large responses
                    )
                    # We still track their activity (timestamps, paths)but dont increment error count or block with AI
                    if r:
                        # add current request timestamp to a sorted set
                        r.zadd(f"{client_ip}:timestamps", {str(time.time()): time.time()})
                        r.expire(f"{client_ip}:timestamps", TIMEFRAME)
                        # add the accessed path to a set for this ip
                        r.sadd(f"{client_ip}:paths", path)
                        r.expire(f"{client_ip}:paths", TIMEFRAME)

                    return Response(
                        content=response.content,
                        status_code=response.status_code,
                        headers=dict(response.headers)
                    )
                except requests.exceptions.RequestException as e:
                    return Response(content=f"An error occurred while proxying: {e}", status_code=status.HTTP_502_BAD_GATEWAY)


    # API key authentication logic
    api_key = request.headers.get("x-api-key") # get the apikey from the x-api-key header

    if not api_key:
        raise HTTPException(status_code=401, detail="Unauthorized: API Key missing")
    
    # check is redis is up and running before trying to validate the key
    if not r:
        print("Warning: Redis not connected, cannot validate API key.")
        raise HTTPException(status_code=500, detail="internal Server Error: Authentication service unavailbale")
    
    #  check the apikey against redis
    client_id = r.get(f"api_key:{api_key}")

    if not client_id:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid API key")

    print(f"Request from client_id: {client_id} using API key: {api_key}")

    # rate limiting logic
    if RATE_LIMIT_ENABLED and r:
        # usicng client id for rate limiting
        rate_limit_key_id = f"rate_limit:{client_id}"

        # using client ip for rate limiting
        # rate_limit_key_id = f"rate_limit:{client_ip}"

        # using a redis pipeline for efficiency
        pipe = r.pipeline()
        pipe.incr(rate_limit_key_id) # increment the counter
        pipe.expire(rate_limit_key_id, RATE_LIMIT_WINDOW_SECONDS) # set/reset the expiry time

        current_requests, _ = pipe.execute()

        if current_requests > RATE_LIMIT_PER_MINUTE:
            print(f"Rate limit exceeded for {rate_limit_key_id}. Current: {current_requests}, Limit: {RATE_LIMIT_PER_MINUTE}")
            if r:
                r.incr("analytics:total_requests_blocked")
            raise HTTPException(status_code=429, detail=f"Too many requests: Limit {RATE_LIMIT_PER_MINUTE} per {RATE_LIMIT_WINDOW_SECONDS} seconds")


    if r:
        # Increment the total requests counter in Redis
        r.incr("analytics:total_requests")
        
    # advanced AI prediction logic
    user_agent = request.headers.get("user-agent", "")
    content_type = request.headers.get("content-type", "")

    # analyzing user_agent
    is_empty_user_agent = 1 if not user_agent else 0
    user_agent_length = len(user_agent)

    # analyzing request body (only for POST/PUT/PATCH)
    body_bytes = b''
    request_body_size = 0
    is_json_content_type = 0
    if request.method in ["POST", "PUT", "PATCH"]:
        # read once, store it, and then pass it to requests.request
        body_bytes = await request.body()
        request_body_size = len(body_bytes)
        request._body = body_bytes

        if "application/json" in content_type.lower():
            is_json_content_type = 1

    # analyzing headers
    num_headers = len(request.headers)
    

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
            [[request_frequency, error_rate, unique_paths,
              is_empty_user_agent, user_agent_length, request_body_size,
              is_json_content_type, num_headers]],
            columns=['request_frequency', 'error_rate', 'unique_paths_accessed',
                     'is_empty_user_agent', 'user_agent_length',
                     'request_body_size', 'is_json_content_type', 'num_headers']
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
            data=body_bytes if request.method in ["POST", "PUT", "PATCH"] else None,
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
        return Response(content=f"An error occurred while proxying: {e}", status_code=status.HTTP_502_BAD_GATEWAY)