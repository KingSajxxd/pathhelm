# PathHelm 🛡️

An intelligent, AI-powered API gateway with a live analytics dashboard, designed to protect and control web traffic.

## What is PathHelm?

PathHelm is a lightweight, containerized API gateway that sits in front of your services. Instead of using simple, fixed rules, it uses a machine learning model to analyze incoming traffic patterns in real-time. It learns to distinguish between normal user behavior and malicious activity like bot attacks, credential stuffing, and denial-of-service attempts, blocking threats before they reach your application.

The entire gateway is designed to be stateless, offloading all state management to a Redis instance, which makes it scalable and resilient.

---

## 📋 Table of Contents

<details>
<summary><strong>🚀 Quick Start Guide</strong></summary>

### Core Features

- 🧠 **AI-Powered Anomaly Detection**: Uses a pre-trained IsolationForest model to identify and block suspicious traffic patterns based on frequency, error rates, and path diversity.

- 🔑 **API Key Authentication**: Secures API access by validating unique API keys provided in request headers against a Redis store. Requests without a valid key are rejected.

- ⏳ **Sophisticated Rate Limiting**: Protects backend services from abuse by limiting the number of requests per API key within a configurable time window (e.g., 100 requests per minute). Returns 429 Too Many Requests when limits are exceeded.

- 🛡️ **IP Whitelisting & Blacklisting**: Allows administrators to explicitly allow (whitelist) or deny (blacklist) specific IP addresses, providing immediate control over access. Whitelisted IPs can bypass other checks.

- 📜 **Persistent Historical Analytics**: A dedicated background service collects and stores gateway metrics into a SQLite database, providing long-term historical data for analysis and trends.

- 📄 **Structured & Centralized Logging**: All gateway logs are now in a JSON format, making them machine-readable and ready for ingestion into a centralized logging platform like the ELK Stack or Grafana Loki.

- 📊 **Enhanced Analytics**: The live dashboard now accurately tracks and displays all blocked requests, whether by IP blacklist, rate limiting, or AI anomaly detection.

- 🔒 **Secured Status Endpoint**: The `/pathhelm/status` endpoint, which provides internal analytics, is now restricted to administrators only via a dedicated `X-Admin-Api-Key`.

- ⚙️ **Stateless Architecture**: All IP tracking and analytics data is stored in Redis, allowing PathHelm instances to be scaled horizontally without data loss.

- 💾 **Persistent State**: Utilizes Docker volumes to ensure that all Redis data (IP history, analytics, API keys, IP lists) survives container restarts.

- 📊 **Live Analytics Dashboard**: A real-time web dashboard built with Streamlit provides live metrics and charts on gateway activity.

- 🔧 **Environment-Based Configuration**: Easily configure the gateway using a `.env` file without changing any code.

- 🐳 **Fully Containerized**: The entire stack (Gateway, Backend, DB, Dashboard) is defined in a single `docker-compose.yml` file for one-command deployment.

### Architecture

```
                           +-------------------+
                           |       User        |
                           +-------------------+
                                    |
                                    | (Request)
                                    v
+-------------------------------------------------------------------------+
| Your Server / Docker Host                                               |
|                                                                         |
|  +------------------+   +-------------------+      +-------------------+|
|  | Dashboard (8501) |<--|   PathHelm (AI)   |<---->|   Redis DB        ||
|  | (Streamlit)      |   |   (Port 8000)     |      |   (Port 6379)     ||
|  +------------------+   +-------------------+      +-------------------+|
|                              | (Forwarded if safe)                      |
|                              v                                          |
|                         +-------------------+                           |
|                         |   Your Backend    |                           |
|                         |   Application     |                           |
|                         +-------------------+                           |
|                                                                         |
+-------------------------------------------------------------------------+
```

### Tech Stack

- **Backend & API**: Python with FastAPI
- **AI/ML**: Scikit-learn, Pandas
- **Database / State Management**: Redis
- **Dashboard**: Streamlit
- **Deployment**: Docker, Docker Compose
- **Testing**: Postman

### Getting Started

#### Prerequisites

- Docker
- Docker Compose (V2 - i.e., the `docker compose` command)

#### How to Run

1. **Clone the repository:**
   ```bash
   git clone https://github.com/KingSajxxd/pathhelm.git
   cd pathhelm
   ```

2. **Create your configuration file:**
   Copy the example environment file to create your local configuration.
   ```bash
   cp .env.example .env
   ```
   
   **IMPORTANT**: Edit your `.env` file to set `ADMIN_API_KEY` and a `your_super_secret_api_key_12345` for `API_KEY` testing. The defaults work out-of-the-box.

3. **Run with Docker Compose:**
   This single command builds and starts the PathHelm gateway, the mock backend, the Redis database, and the analytics dashboard.
   ```bash
   docker compose up --build
   ```

4. **Set up API Keys in Redis:**
   PathHelm uses Redis to store API keys. You need to add at least one API key for testing.

   **Find your Redis container name:**
   ```bash
   docker compose ps
   ```
   Look for the Redis container name (e.g., `pathhelm-redis-1`).

   **Access Redis CLI:**
   ```bash
   docker exec -it pathhelm-redis-1 redis-cli
   ```
   (Replace with your actual Redis container name)

   **Add an API key:**
   ```
   SET "api_key:your_super_secret_api_key_12345" "test-client"
   ```
   
   **Verify the key (optional):**
   ```
   GET "api_key:your_super_secret_api_key_12345"
   ```
   Should return `"test-client"`.

   **Exit Redis CLI:**
   ```
   exit
   ```

### How to Use

#### Access the Services

- **API Gateway**: http://localhost:8000
- **Live Dashboard**: http://localhost:8501

#### Test the Gateway

- **Normal Authenticated Request**: Send a GET request to `http://localhost:8000/some/path` with a valid API Key (e.g., `your_super_secret_api_key_12345`) in the `X-API-Key` header. It will be forwarded and return a 200 OK.

- **Missing API Key**: Send a request without the `X-API-Key` header. Expected: 401 Unauthorized.

- **Invalid API Key**: Send a request with a wrong `X-API-Key` value. Expected: 403 Forbidden.

- **Simulate Rate Limit**: Use the Postman Runner (or curl in a loop) to send rapid requests with a valid API Key to `http://localhost:8000/api/test/{{$randomInt}}`. Configure `RATE_LIMIT_PER_MINUTE` in your `.env` to a low number (e.g., 5) for easy testing. Observe 429 Too Many Requests responses after hitting the configured limit. The "Total Requests Blocked" counter on the dashboard will now increment for these.

#### Managing IP Blacklist/Whitelist (Admin Access Required)

**Admin API Key**: Use the `ADMIN_API_KEY` from your `.env` in the `X-Admin-Api-Key` header for these requests.

**Important Note on IPs**: When testing from your Docker host, the IP seen by the pathhelm container might be an internal Docker IP (e.g., `172.17.0.1` or `192.168.65.1`). Check the pathhelm container logs for `Incoming request from client_ip: YOUR_DOCKER_INTERNAL_IP` to get the correct IP to blacklist/whitelist.

##### Blacklist Management

- **Add to Blacklist**: `POST` to `http://localhost:8000/pathhelm/admin/ip_blacklist?ip=YOUR_IP_TO_BLOCK`
- **Remove from Blacklist**: `DELETE` to `http://localhost:8000/pathhelm/admin/ip_blacklist?ip=YOUR_IP_TO_UNBLOCK`
- **Get Blacklist**: `GET` to `http://localhost:8000/pathhelm/admin/ip_blacklist`

##### Whitelist Management

- **Add to Whitelist**: `POST` to `http://localhost:8000/pathhelm/admin/ip_whitelist?ip=YOUR_IP_TO_ALLOW`
- **Remove from Whitelist**: `DELETE` to `http://localhost:8000/pathhelm/admin/ip_whitelist?ip=YOUR_IP_TO_UNALLOW`
- **Get Whitelist**: `GET` to `http://localhost:8000/pathhelm/admin/ip_whitelist`

##### Testing IP Lists

- **Test Blacklisted IP**: Once an IP is blacklisted, requests from that IP (even with a valid API key) should receive 403 Forbidden. The "Total Requests Blocked" counter on the dashboard will now increment for these.

- **Test Whitelisted IP**: Once an IP is whitelisted, requests from that IP should always be allowed, bypassing API key, rate limit, and AI checks.

#### Test Secured Status Endpoint (Admin Access Required)

- **Access Status (No Key)**: Try to visit `http://localhost:8000/pathhelm/status` directly in your browser or with curl without any `X-Admin-Api-Key` header. Expected: 401 Unauthorized.

- **Access Status (Valid Admin Key)**: Use `curl -H "X-Admin-Api-Key: YOUR_ADMIN_KEY"` to `http://localhost:8000/pathhelm/status`. Expected: 200 OK with JSON data.

- **Dashboard Functionality**: Ensure your Streamlit dashboard at `http://localhost:8501` is now fetching data correctly. It has been updated to send the `X-Admin-Api-Key`.

#### Simulate an Attack (AI Detection)

1. Use the Postman Runner to send a burst of 30+ requests to `http://localhost:8000/api/test/{{$randomInt}}` with a valid `X-API-Key`.

2. **Observe Dashboard**: Watch the Live Dashboard at `http://localhost:8501`. You will see the "Total Requests" and "Blocked Requests" counters increase in real-time as the AI identifies and blocks the attack.

#### Observe Structured Logs

After generating traffic, view the logs for the pathhelm service:

```bash
docker logs pathhelm-pathhelm-1 --tail 50
```

You will now see log lines in a machine-readable JSON format, containing detailed information about each request (e.g., client IP, method, path, status code, and security actions).

#### Test Persistent Dashboard History

1. Generate some traffic (normal, blocked, etc.) and let the history-collector run for at least a few minutes (the default interval is 60 seconds).

2. Stop the containers with `docker compose down`.

3. Restart them with `docker compose up`.

4. Check the dashboard again. The live counters will be reset, but the historical charts and table will show the data you generated before the restart.

</details>

---

<details>
<summary><strong>🔧 Integration with Your Backend</strong></summary>

## PathHelm 🛡️ Integration Guide

This document provides a step-by-step guide on how to integrate PathHelm, an AI-powered API gateway, with your own backend services using Docker Compose.

### 🚀 1. Understanding the Setup

PathHelm acts as a reverse proxy that sits in front of your application. It intercepts all incoming requests, applies security policies (like API key validation, rate limiting, and AI anomaly detection), and then forwards legitimate requests to your backend service.

#### Architecture Overview:

```
                           +-------------------+
                           |       User        |
                           +-------------------+
                                    |
                                    | (Request to PathHelm:8000)
                                    v
+-------------------------------------------------------------------------+
| Your Server / Docker Host                                               |
|                                                                         |
|  +------------------+   +-------------------+      +-------------------+|
|  | Dashboard (8501) |<--|   PathHelm (AI)   |<---->|   Redis DB        ||
|  | (Streamlit)      |   |   (Port 8000)     |      |   (Port 6379)     ||
|  +------------------+   +-------------------+      +-------------------+|
|                              | (Forwarded if safe)                      |
|                              v                                          |
|                         +-------------------+                           |
|                         |   Your Backend    |                           |
|                         |   Application     |                           |
|                         |   (Port 8001)     |                           |
|                         +-------------------+                           |
|                                                                         |
+-------------------------------------------------------------------------+
```

### 🛠️ 2. Preparing Your Backend Service

Your backend service needs to be containerized and configured to listen on a specific internal port that PathHelm can forward to. For this guide, we'll assume your backend will listen on port 8001.

#### Adjust Your Backend's Listening Port:
Modify your backend application's code to ensure it binds to 0.0.0.0 and listens on port 8001.

**Example (Python/FastAPI):**
If your backend uses Uvicorn/FastAPI, find the uvicorn.Config line and set port=8001:

```python
# In your_backend_app/main.py (or similar)
import uvicorn
from your_backend_app.api.main import app as backend_app

async def main():
    # ...
    config = uvicorn.Config(backend_app, host="0.0.0.0", port=8001, log_level="info")
    # ...
    api_server = uvicorn.Server(config)
    # ...
```

Adjust this step based on your backend's language and framework.

#### Create a Dockerfile for Your Backend:
In the root directory of your backend application (e.g., `your-backend-service/`), create a file named `Dockerfile`. This file tells Docker how to build an image for your service.

**Example Dockerfile (for a Python backend with requirements.txt):**

```dockerfile
# your-backend-service/Dockerfile
FROM python:3.10-slim-buster

WORKDIR /app

# Copy dependency file and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY . .

# Command to run your application
CMD ["python", "main.py"] # Adjust to your backend's entry point
```

**Example Dockerfile (for a Node.js backend):**

```dockerfile
# your-backend-service/Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 8001 # Expose the port your Node.js app listens on
CMD ["npm", "start"] # Or "node index.js"
```

### ⚙️ 3. Configuring PathHelm for Integration

To integrate your backend, you'll create a duplicated PathHelm project and modify its docker-compose.yml to include and point to your backend service.

#### Duplicate the PathHelm Project:
Navigate to the directory containing your original pathhelm-1 folder (and your your-backend-service folder). Then, create a copy of the PathHelm project:

```bash
# Example: If your projects are in /my_projects/pathhelm-1 and /my_projects/your-backend-service
cd /path/to/my_projects/
cp -r pathhelm-1 pathhelm-integration
```

All further modifications will be done in the `pathhelm-integration` directory.

#### Edit docker-compose.yml in pathhelm-integration:
Open the `pathhelm-integration/docker-compose.yml` file.

**Remove the mock_backend service:**
Locate and completely remove or comment out the `mock_backend` service block.

```yaml
#  mock_backend:
#    build:
#      context: .
#      dockerfile: Dockerfile.backend
#    ports:
#      - "8001:8001"
#    networks:
#      - pathhelm-network
```

**Add Your Backend Service:**
Add a new service definition for your backend. We'll name it `your_backend_service` (you can choose any name, but remember it for TARGET_URL). Adjust the context to point to your backend's Dockerfile directory.

```yaml
  your_backend_service: # <-- Your chosen service name
    build:
      context: ../your-backend-service # Relative path to your backend's Dockerfile
    ports:
      - "8001:8001" # Expose if you need direct access for debugging
    networks:
      - pathhelm-network # Connect to the shared network
    # Optional: Add environment variables needed by your backend
    # environment:
    #   - DB_HOST=your_db_service_name
```

**Update PathHelm's TARGET_URL:**
In the `pathhelm` service block, modify the `TARGET_URL` environment variable to point to your newly added backend service and its internal port (8001).

```yaml
  pathhelm:
    build: .
    ports:
      - "8000:8000"
    environment:
      # ... (your other PathHelm environment variables from .env) ...
      - TARGET_URL=http://your_backend_service:8001 # <-- Point to your backend
    depends_on:
      - your_backend_service # <-- Add this dependency
      - redis
    env_file:
      - .env
    networks: # <-- CRUCIAL: Ensure pathhelm joins the network
      - pathhelm-network
```

**Ensure all services are on pathhelm-network:**
Verify that `redis`, `dashboard`, and `history-collector` services also have `networks: - pathhelm-network` defined under them. This ensures all components can communicate.

```yaml
  redis:
    # ...
    networks:
      - pathhelm-network

  dashboard:
    # ...
    networks:
      - pathhelm-network

  history-collector:
    # ...
    networks:
      - pathhelm-network
```

**Verify Root-level networks Definition:**
Ensure the networks block is defined at the very bottom of your docker-compose.yml, aligned with services:.

```yaml
# ... (all your services blocks) ...

networks:
  pathhelm-network:
    driver: bridge
```

#### Create PathHelm's .env File:
In your `pathhelm-integration` directory, copy the example environment file:

```bash
cp .env.example .env
```

Open this `.env` file and set your `ADMIN_API_KEY` and a default `API_KEY` for testing. You can also adjust `RATE_LIMIT_PER_MINUTE` and `RATE_LIMIT_ENABLED` for testing different scenarios.

### ▶️ 4. Running the Integrated Stack

Once all files are configured, you can launch the entire system.

#### Navigate to the Integration Directory:

```bash
cd /path/to/my_projects/pathhelm-integration
```

#### Clean Up Previous Runs (Recommended):
If you've run Docker Compose before, ensure a clean state:

```bash
docker compose down --volumes --remove-orphans
```

#### Build and Start Services:

```bash
docker compose up --build
```

This command will build your backend's image, PathHelm's image, and then start all services.

### 🔑 5. Setting Up API Keys in Redis

PathHelm uses Redis to store API keys and their associated client IDs. You need to manually add these to Redis.

#### Find Your Redis Container Name:
While your services are running, open a new terminal tab and list your Docker Compose services:

```bash
cd /path/to/my_projects/pathhelm-integration
docker compose ps
```

Look for the name of your Redis container (e.g., `pathhelm-integration-redis-1`).

#### Access the Redis CLI:

```bash
docker exec -it pathhelm-integration-redis-1 redis-cli
```

(Replace with your actual Redis container name). You'll see the `127.0.0.1:6379>` prompt.

#### Set an API Key:
Use the SET command. PathHelm expects the key to be prefixed with `api_key:`.

```
SET "api_key:your_chosen_api_key_value" "your_client_id_here"
```

Replace `your_chosen_api_key_value` with the API key you want to use (e.g., `my-app-key-123`).

Replace `your_client_id_here` with an identifier for the client (e.g., `my-frontend-app`).

**Example:** `SET "api_key:my-app-key-123" "frontend-app"`

#### Verify (Optional):

```
GET "api_key:my-app-key-123"
```

It should return `"frontend-app"`.

#### Exit Redis CLI:

```
exit
```

### ✅ 6. Testing the Integration

Now you can test PathHelm's features by sending requests to http://localhost:8000, which will be handled by PathHelm and then forwarded to your backend.

- **API Gateway (PathHelm)**: http://localhost:8000
- **PathHelm Live Dashboard**: http://localhost:8501

Use Postman or curl for testing. Remember to replace `your_backend_endpoint` with an actual endpoint from your backend (e.g., `/status`, `/api/data`).

#### 6.1. Basic Authenticated Request
- **Method**: GET
- **URL**: `http://localhost:8000/your_backend_endpoint`
- **Headers**: `X-API-Key: your_chosen_api_key_value` (from Redis)
- **Expected**: 200 OK from your backend via PathHelm.

#### 6.2. Missing API Key
- **Method**: GET
- **URL**: `http://localhost:8000/your_backend_endpoint`
- **Headers**: (No X-API-Key header)
- **Expected**: 401 Unauthorized from PathHelm.

#### 6.3. Invalid API Key
- **Method**: GET
- **URL**: `http://localhost:8000/your_backend_endpoint`
- **Headers**: `X-API-Key: wrong_key`
- **Expected**: 403 Forbidden from PathHelm.

#### 6.4. Rate Limiting Test
1. Adjust `RATE_LIMIT_PER_MINUTE` in `pathhelm-integration/.env` to a low number (e.g., 5).
2. Restart services (`docker compose down`, `docker compose up --build`).
3. Use Postman Runner to send more requests than the limit within 60 seconds (e.g., 10-20 iterations of `GET http://localhost:8000/your_backend_endpoint` with a valid `X-API-Key`).
4. **Expected**: After hitting the limit, you'll receive 429 Too Many Requests. Check the dashboard (http://localhost:8501) to see blocked requests increase.

#### 6.5. IP Blacklisting (Admin Access)

**Find your Docker internal IP:** Check pathhelm container logs for `Incoming request from client_ip: YOUR_DOCKER_INTERNAL_IP`. Use this IP.

**Add to Blacklist:**
- **Method**: POST
- **URL**: `http://localhost:8000/pathhelm/admin/ip_blacklist?ip=YOUR_DOCKER_INTERNAL_IP`
- **Headers**: `X-Admin-Api-Key: Your ADMIN_API_KEY` (from .env)
- **Expected**: 200 OK.

**Test Blacklisted IP:** Send a request to `http://localhost:8000/your_backend_endpoint` from your machine (even with a valid API key).
- **Expected**: 403 Forbidden. Check the dashboard for blocked requests.

**Remove from Blacklist:**
- **Method**: DELETE
- **URL**: `http://localhost:8000/pathhelm/admin/ip_blacklist?ip=YOUR_DOCKER_INTERNAL_IP`
- **Headers**: `X-Admin-Api-Key: Your ADMIN_API_KEY`
- **Expected**: 200 OK.

#### 6.6. AI Anomaly Detection Test

1. Temporarily disable rate limiting in `pathhelm-integration/.env` (`RATE_LIMIT_ENABLED=false`) and restart (`docker compose down`, `docker compose up --build`). This ensures all traffic reaches the AI.

2. **Simulate an anomalous attack:** Use Postman Runner to send a very high volume of requests (e.g., 500-1500+) in a short period. Crucially, vary the paths in your requests, hitting many different (including non-existent or "silly") endpoints to increase "path diversity." Also, consider introducing requests that would cause backend errors (e.g., hitting clearly invalid URLs) to raise the error_rate metric.

**Example Attack with Postman Runner:**

Create a collection of requests targeting diverse endpoints:
- `GET http://localhost:8000/your_backend_endpoint`
- `GET http://localhost:8000/non_existent_path_1`
- `GET http://localhost:8000/api/v1/user/{{$randomInt}}`
- `GET http://localhost:8000/another_silly_path`

Run the collection with a high number of iterations (e.g., 500+).
Ensure each request has a valid `X-API-Key`.

**Expected:** After a certain number of requests (as the AI's features accumulate), you should start seeing 403 Forbidden responses from PathHelm, indicating AI anomaly detection.

**Check PathHelm Logs:** Look for messages like "ANOMALY DETECTED from IP: ...".

**Check Dashboard:** The "Total Requests Blocked" counter should increment, reflecting blocks by AI.

</details>

---

## Future Roadmap

- [ ] **Unit & Integration Testing**: Implement pytest to create a robust test suite for the gateway logic.

- [ ] **CI/CD Pipeline**: Set up GitHub Actions to automatically run tests and publish the Docker image to Docker Hub.

- [ ] **Advanced Rule Engine**: Allow users to add more granular custom blocking rules (e.g., by country, specific header values, or request body patterns) alongside the AI model and IP lists.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b NewFeature`)
3. Commit your Changes (`git commit -m 'Add some NewFeature'`)
4. Push to the Branch (`git push origin NewFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See LICENSE for more information.