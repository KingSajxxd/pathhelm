# PathHelm 🛡️

**An intelligent, AI-powered API gateway and security proxy designed to protect and control web traffic.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-311/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

---

## What is PathHelm?

PathHelm is a lightweight, containerized API gateway that sits in front of your services. Instead of using simple, fixed rules, it uses a machine learning model to analyze incoming traffic patterns in real-time. It learns to distinguish between normal user behavior and malicious activity like bot attacks, credential stuffing, and denial-of-service attempts, blocking threats before they reach your application.

The entire gateway is designed to be **stateless**, offloading all state management to a Redis instance, which makes it scalable and resilient.

## Core Features

* **🧠 AI-Powered Anomaly Detection:** Uses a pre-trained `IsolationForest` model to identify and block suspicious traffic patterns based on frequency, error rates, and path diversity.
* **⚙️ Stateless Architecture:** All IP tracking and analytics data is stored in Redis, allowing PathHelm instances to be scaled horizontally without data loss.
* **💾 Persistent State:** Utilizes Docker volumes to ensure that all Redis data (IP history, analytics) survives container restarts.
* **🐳 Fully Containerized:** The entire stack (Gateway, Backend, Redis) is defined in a single `docker-compose.yml` file for one-command deployment.
* **📊 Live Analytics:** A built-in `/pathhelm/status` endpoint provides real-time metrics on processed and blocked requests, fetched directly from Redis.
* **🔌 Easy Integration:** Protect any backend service by simply routing traffic through PathHelm.

## Architecture

                           +-------------------+
                           |       User        |
                           +-------------------+
                                    |
                                    | (Request)
                                    v

+-------------------------------------------------------------------------+
| Your Server / Docker Host                                               |
|                                                                         |
|       +-------------------+      +-------------------+                  |
|       |   PathHelm (AI)   |<---->|   Redis DB        | (Stateful)       |
|       |   (Port 8000)     |      |   (Port 6379)     |                  |
|       +-------------------+      +-------------------+                  |
|            | (Forwarded if safe)                                        |
|            v                                                            |
|       +-------------------+                                             |
|       |   Your Backend    |                                             |
|       |   Application     |                                             |
|       +-------------------+                                             |
|                                                                         |
+-------------------------------------------------------------------------+


## Tech Stack

* **Backend & API:** Python with FastAPI
* **AI/ML:** Scikit-learn, Pandas
* **Database / State Management:** Redis
* **Deployment:** Docker, Docker Compose
* **Testing:** Postman

## Getting Started

### Prerequisites

* Docker
* Docker Compose (V2 - i.e., the `docker compose` command)

### How to Run

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/KingSajxxd/pathhelm.git](https://github.com/KingSajxxd/pathhelm.git)
    cd pathhelm
    ```

2.  **Run with Docker Compose:**
    This single command builds and starts the PathHelm gateway, the mock backend service, and the Redis database.
    ```bash
    docker compose up --build
    ```
    PathHelm will be available at `http://localhost:8000`.

## How to Use

1.  **Test the Gateway:**
    * **Normal Request:** Send a `GET` request to `http://localhost:8000/some/path`. It will be forwarded to the backend and return a `200 OK`.
    * **Simulate an Attack:** Use the Postman Runner to send a burst of 30+ requests to `http://localhost:8000/api/test/{{$randomInt}}`. You will see the first few requests pass, followed by `403 Forbidden` errors as PathHelm's AI detects the anomaly.

2.  **Check the Status:**
    Send a `GET` request to `http://localhost:8000/pathhelm/status` to see live analytics fetched from Redis.
    ```json
    {
        "total_requests_processed": 30,
        "total_requests_blocked": 18,
        "currently_tracking_ips": 1
    }
    ```

3.  **Test Persistence:**
    * Run the Postman test to generate some stats.
    * Stop the containers with `docker compose down`.
    * Restart them with `docker compose up`.
    * Check `/pathhelm/status` again. The analytics data will still be there!

## Configuration

Currently, the `TARGET_SERVICE_URL` is hardcoded in `app/main.py`. Future versions will use environment variables for easier configuration.

## Future Roadmap

* [ ] **Web Dashboard:** Create a simple web UI (e.g., with Streamlit) to visualize the analytics data.
* [ ] **Environment-based Configuration:** Use a `.env` file to manage settings like the target URL and Redis connection details.
* [ ] **Advanced Rule Engine:** Allow users to add custom rules alongside the AI model.
* [ ] **CI/CD Pipeline:** Set up GitHub Actions to automatically build and test the Docker image on push.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'feat: Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.
