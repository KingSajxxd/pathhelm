# PathHelm 🛡️

An intelligent, AI-powered API gateway with a live analytics dashboard, designed to protect and control web traffic.

## What is PathHelm?

PathHelm is a lightweight, containerized API gateway that sits in front of your services. Instead of using simple, fixed rules, it uses a machine learning model to analyze incoming traffic patterns in real-time. It learns to distinguish between normal user behavior and malicious activity like bot attacks, credential stuffing, and denial-of-service attempts, blocking threats before they reach your application.

The entire gateway is designed to be stateless, offloading all state management to a Redis instance, which makes it scalable and resilient.

## Core Features

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

## Architecture

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

## Tech Stack

- **Backend & API**: Python with FastAPI
- **AI/ML**: Scikit-learn, Pandas
- **Database / State Management**: Redis
- **Dashboard**: Streamlit
- **Deployment**: Docker, Docker Compose
- **Testing**: Postman

## Getting Started

### Prerequisites

- Docker
- Docker Compose (V2 - i.e., the `docker compose` command)

### How to Run

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

## How to Use

### Access the Services

- **API Gateway**: http://localhost:8000
- **Live Dashboard**: http://localhost:8501

### Test the Gateway

- **Normal Authenticated Request**: Send a GET request to `http://localhost:8000/some/path` with a valid API Key (e.g., `your_super_secret_api_key_12345`) in the `X-API-Key` header. It will be forwarded and return a 200 OK.

- **Missing API Key**: Send a request without the `X-API-Key` header. Expected: 401 Unauthorized.

- **Invalid API Key**: Send a request with a wrong `X-API-Key` value. Expected: 403 Forbidden.

- **Simulate Rate Limit**: Use the Postman Runner (or curl in a loop) to send rapid requests with a valid API Key to `http://localhost:8000/api/test/{{$randomInt}}`. Configure `RATE_LIMIT_PER_MINUTE` in your `.env` to a low number (e.g., 5) for easy testing. Observe 429 Too Many Requests responses after hitting the configured limit. The "Total Requests Blocked" counter on the dashboard will now increment for these.

### Managing IP Blacklist/Whitelist (Admin Access Required)

**Admin API Key**: Use the `ADMIN_API_KEY` from your `.env` in the `X-Admin-Api-Key` header for these requests.

**Important Note on IPs**: When testing from your Docker host, the IP seen by the pathhelm container might be an internal Docker IP (e.g., `172.17.0.1` or `192.168.65.1`). Check the pathhelm container logs for `Incoming request from client_ip: YOUR_DOCKER_INTERNAL_IP` to get the correct IP to blacklist/whitelist.

#### Blacklist Management

- **Add to Blacklist**: `POST` to `http://localhost:8000/pathhelm/admin/ip_blacklist?ip=YOUR_IP_TO_BLOCK`
- **Remove from Blacklist**: `DELETE` to `http://localhost:8000/pathhelm/admin/ip_blacklist?ip=YOUR_IP_TO_UNBLOCK`
- **Get Blacklist**: `GET` to `http://localhost:8000/pathhelm/admin/ip_blacklist`

#### Whitelist Management

- **Add to Whitelist**: `POST` to `http://localhost:8000/pathhelm/admin/ip_whitelist?ip=YOUR_IP_TO_ALLOW`
- **Remove from Whitelist**: `DELETE` to `http://localhost:8000/pathhelm/admin/ip_whitelist?ip=YOUR_IP_TO_UNALLOW`
- **Get Whitelist**: `GET` to `http://localhost:8000/pathhelm/admin/ip_whitelist`

#### Testing IP Lists

- **Test Blacklisted IP**: Once an IP is blacklisted, requests from that IP (even with a valid API key) should receive 403 Forbidden. The "Total Requests Blocked" counter on the dashboard will now increment for these.

- **Test Whitelisted IP**: Once an IP is whitelisted, requests from that IP should always be allowed, bypassing API key, rate limit, and AI checks.

### Test Secured Status Endpoint (Admin Access Required)

- **Access Status (No Key)**: Try to visit `http://localhost:8000/pathhelm/status` directly in your browser or with curl without any `X-Admin-Api-Key` header. Expected: 401 Unauthorized.

- **Access Status (Valid Admin Key)**: Use `curl -H "X-Admin-Api-Key: YOUR_ADMIN_KEY"` to `http://localhost:8000/pathhelm/status`. Expected: 200 OK with JSON data.

- **Dashboard Functionality**: Ensure your Streamlit dashboard at `http://localhost:8501` is now fetching data correctly. It has been updated to send the `X-Admin-Api-Key`.

### Simulate an Attack (AI Detection)

1. Use the Postman Runner to send a burst of 30+ requests to `http://localhost:8000/api/test/{{$randomInt}}` with a valid `X-API-Key`.

2. **Observe Dashboard**: Watch the Live Dashboard at `http://localhost:8501`. You will see the "Total Requests" and "Blocked Requests" counters increase in real-time as the AI identifies and blocks the attack.

### Observe Structured Logs

After generating traffic, view the logs for the pathhelm service:

```bash
docker logs pathhelm-pathhelm-1 --tail 50
```

You will now see log lines in a machine-readable JSON format, containing detailed information about each request (e.g., client IP, method, path, status code, and security actions).

### Test Persistent Dashboard History

1. Generate some traffic (normal, blocked, etc.) and let the history-collector run for at least a few minutes (the default interval is 60 seconds).

2. Stop the containers with `docker compose down`.

3. Restart them with `docker compose up`.

4. Check the dashboard again. The live counters will be reset, but the historical charts and table will show the data you generated before the restart.

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