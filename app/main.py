# app/main.py
import re
import requests
from fastapi import FastAPI, Request, Response
from starlette.routing import Host
from urllib3 import response

# the service to protect. From Docker's network
TARGET_SERVICE_URL = "http://mock-backend:5000"

app = FastAPI(title="PathHelm Gateway")

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(request: Request, path: str):
    """
    captures all incoming requests and forwards 
    them to the target service
    """
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

        # return the response from the target service back to the client
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except requests.exceptions.RequestException as e:
        # If the backend service is down, return a 502 Bad Gateway error
        return Response(content=f"An error occurred while proxying: {e}", status_code=502)