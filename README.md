# PathHelm 🛡️

**An intelligent, AI-powered API gateway with a live analytics dashboard, designed to protect and control web traffic.**

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
* **📊 Live Analytics Dashboard:** A real-time web dashboard built with Streamlit provides live metrics and charts on gateway activity.
* **🔧 Environment-Based Configuration:** Easily configure the gateway using a `.env` file without changing any code.
* **🐳 Fully Containerized:** The entire stack (Gateway, Backend, DB, Dashboard) is defined in a single `docker-compose.yml` file for one-command deployment.

```bash
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

* **Backend & API:** Python with FastAPI
* **AI/ML:** Scikit-learn, Pandas
* **Database / State Management:** Redis
* **Dashboard:** Streamlit
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

2.  **Create your configuration file:**
    Copy the example environment file to create your local configuration.
    ```bash
    cp .env.example .env
    ```
    *(You can modify the `.env` file if your setup is different, but the defaults work out-of-the-box.)*

3.  **Run with Docker Compose:**
    This single command builds and starts the PathHelm gateway, the mock backend, the Redis database, and the analytics dashboard.
    ```bash
    docker compose up --build
    ```

## How to Use

1.  **Access the Services:**
    * **API Gateway:** `http://localhost:8000`
    * **Live Dashboard:** `http://localhost:8501`

2.  **Test the Gateway:**
    * **Normal Request:** Send a `GET` request to `http://localhost:8000/some/path`. It will be forwarded and return a `200 OK`.
    * **Simulate an Attack:** Use the Postman Runner to send a burst of 30+ requests to `http://localhost:8000/api/test/{{$randomInt}}`.
    * **Observe:** Watch the Live Dashboard at `http://localhost:8501`. You will see the "Total Requests" and "Blocked Requests" counters increase in real-time as the AI identifies and blocks the attack.

3.  **Test Persistence:**
    * Run the Postman test to generate some stats.
    * Stop the containers with `docker compose down`.
    * Restart them with `docker compose up`.
    * Check the dashboard again. The analytics data will still be there!

## Future Roadmap

* [ ] **Unit & Integration Testing:** Implement `pytest` to create a robust test suite for the gateway logic.
* [ ] **CI/CD Pipeline:** Set up GitHub Actions to automatically run tests and publish the Docker image to Docker Hub.
* [ ] **Advanced Rule Engine:** Allow users to add custom blocking rules (e.g., by country or IP range) alongside the AI model.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'feat: Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.
