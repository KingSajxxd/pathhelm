# PathHelm 🛡️

**An intelligent, AI-powered API gateway and security proxy designed to protect and control web traffic.**

---

## What is PathHelm?

PathHelm is a lightweight, containerized API gateway that sits in front of your services. Instead of using simple, fixed rules, it uses a machine learning model to analyze incoming traffic patterns in real-time. It learns to distinguish between normal user behavior and malicious activity like bot attacks, credential stuffing, and denial-of-service attempts, blocking threats before they reach your application.

## Core Features

* **🧠 AI-Powered Anomaly Detection:** Uses an `IsolationForest` model to identify and block suspicious traffic patterns.
* **⚙️ Dynamic Rate Limiting:** Goes beyond simple request counting to understand traffic context.
* **🐳 Containerized & Portable:** Runs anywhere with Docker. The entire stack is defined in a single `docker-compose.yml` file for easy deployment.
* **📊 Live Analytics:** A built-in `/pathhelm/status` endpoint provides real-time metrics on processed and blocked requests.
* **🔌 Easy Integration:** Protect any backend service by simply routing traffic through PathHelm.

## Tech Stack

* **Backend:** Python with FastAPI
* **AI/ML:** Scikit-learn, Pandas
* **Deployment:** Docker, Docker Compose
* **Testing:** Postman

## Getting Started

### Prerequisites

* Docker
* Docker Compose (V2)

### How to Run

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/KingSajxxd/pathhelm.git](https://github.com/KingSajxxd/pathhelm.git)
    cd pathhelm
    ```

2.  **Run with Docker Compose:**
    This single command builds and starts the PathHelm gateway and a mock backend service for testing.
    ```bash
    docker compose up --build
    ```
    PathHelm will be available at `http://localhost:8000`.

## How to Use

1.  **Protect Your Service:** In a production `docker-compose.yml`, you would replace the `mock-backend` service with your own application and point PathHelm's `TARGET_SERVICE_URL` to it.

2.  **Test the Gateway:**
    * **Normal Request:** Send a `GET` request to `http://localhost:8000/some/path`. It will be forwarded to the backend and return a `200 OK`.
    * **Simulate an Attack:** Use the Postman Runner to send a burst of 30+ requests to `http://localhost:8000/api/test/{{$randomInt}}`. You will see the first few requests pass, followed by `403 Forbidden` errors as PathHelm's AI detects the anomaly.

3.  **Check the Status:**
    Send a `GET` request to `http://localhost:8000/pathhelm/status` to see live analytics.
    ```json
    {
        "total_requests_processed": 50,
        "total_requests_blocked": 25,
        "currently_tracking_ips": 1
    }
    ```

## Future Roadmap

* [ ] Add a simple web dashboard to visualize analytics.
* [ ] Use Redis instead of in-memory dictionaries for more robust, scalable state management.
* [ ] Allow users to configure settings via a `.env` file or a config API.

---