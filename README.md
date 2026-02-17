# FinOps Intelligence Dashboard

The FinOps Intelligence Dashboard is a comprehensive solution designed to provide multi-dimensional cloud cost aggregation and AI-driven insights. It empowers organizations to gain deeper visibility into their cloud spending, identify cost drivers, detect anomalies, and receive actionable recommendations for cost optimization.

This project consists of a FastAPI backend and a React frontend, integrated with Google Cloud services like BigQuery and Google Generative AI (Gemini).

## Technical Brief

### Detailed Setup and Local Execution Steps

This section outlines how to set up and run the FinOps Intelligence Dashboard locally using Docker Compose, or by running the frontend and backend services independently.

#### Prerequisites

Before you begin, ensure you have the following installed:
*   **Docker & Docker Compose:** Essential for running services in containers.
*   **Node.js (v18 or higher) & npm:** Required for frontend development if running independently.
*   **Python (v3.11 or higher) & pip:** Required for backend development if running independently.
*   **Google Cloud Account & Project:** Necessary for BigQuery and Google Generative AI integration.
*   **Service Account Key:** A JSON key file for a Google Cloud service account with permissions to access BigQuery and Google GeneropsAI. Place this file (e.g., `service-account-file.json`) in the `backend/` directory.
*   **Google Generative AI API Key:** An API key for authenticating with the Gemini model.

#### Environment Variables

Both the backend and frontend require specific environment variables. Create a `.env` file in the `backend/` directory and another in `frontend/` if running independently, or ensure they are set in your shell environment before using Docker Compose.

**`backend/.env` (or environment variables for backend service):**
```
DATABASE_URL="postgresql+psycopg2://user:password@db:5432/finops_db"
GOOGLE_APPLICATION_CREDENTIALS="/app/service-account-file.json" # Path within container
GOOGLE_API_KEY="YOUR_GOOGLE_GENERATIVE_AI_API_KEY"
GCP_PROJECT_ID="YOUR_GCP_PROJECT_ID"
LLM_MODEL_NAME="gemini-2.5-flash" # Optional: Specify Gemini model
```

**`frontend/.env.development` (for independent frontend development):**
```
VITE_API_BASE_URL="http://localhost:8000/api/v1" # Adjust if your backend port differs
```

#### Running Services Independently

You can also run the backend and frontend services separately without Docker Compose.

##### Database (PostgresDB)

1.  **Run database using docker compose file:**
    ```bash
    docker-compose up -d
    ```

##### Backend (FastAPI)

1.  **Navigate to Backend Directory:**
    ```bash
    cd backend
    ```
2.  **Create and Activate Virtual Environment:**
    ```bash
    python -m venv venv
    ./venv/Scripts/activate # On Windows
    # source venv/bin/activate # On macOS/Linux
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set Environment Variables:** Ensure `DATABASE_URL`, `GOOGLE_APPLICATION_CREDENTIALS` (absolute path to your JSON key), `GOOGLE_API_KEY`, and `GCP_PROJECT_ID` are set in your shell environment or in a `.env` file that FastAPI can load.
    *   For `DATABASE_URL`, if running PostgreSQL locally without Docker Compose, you'll need to install and run PostgreSQL directly and adjust the URL accordingly (e.g., `postgresql+psycopg2://user:password@localhost:5432/finops_db`).
5.  **Run Migrations (if needed):**
    ```bash
    alembic upgrade head
    ```
6.  **Start the FastAPI Application:**
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
    ```
    The backend API will be available at `http://localhost:8080` (or the port you configured).

##### Frontend (React)

1.  **Navigate to Frontend Directory:**
    ```bash
    cd frontend
    ```
2.  **Install Dependencies:**
    ```bash
    npm install
    ```
3.  **Set Environment Variables:** Create a `.env.development` file with `VITE_API_BASE_URL` pointing to your running backend (e.g., `VITE_API_BASE_URL="http://localhost:8080/api/v1"`).
4.  **Start the React Development Server:**
    ```bash
    npm run dev
    ```
    The frontend will be available at `http://localhost:5173`.

### Architecture & SDLC Overview

#### Application Architecture

The FinOps Intelligence Dashboard follows a modern, decoupled architecture consisting of a React frontend, a FastAPI backend, and a PostgreSQL database, heavily leveraging Google Cloud Platform services.

*   **Frontend:** Developed with **React 19**, **Vite** for fast development, **MUI (Material-UI)** for the component library, and **`@tanstack/react-query`** for efficient data fetching and state management. It communicates with the FastAPI backend via RESTful APIs.
*   **Backend:** Built with **FastAPI** (Python 3.11), providing a high-performance. It manages data persistence with **SQLAlchemy** (ORM) and **PostgreSQL**. Key functionalities include:
    *   **Data Aggregation:** Connects to **Google BigQuery** to ingest and aggregate cloud billing data.
    *   **AI-Driven Insights:** Integrates with **Google Generative AI (Gemini Model)** to generate spend summaries, anomaly detection, predictive forecasting, and cost optimization recommendations.
*   **Database:** **PostgreSQL** serves as the primary database for storing aggregated FinOps data and application-specific information.
*   **Cloud Platform:** Primarily deployed on **Google Cloud Run**, providing a fully managed, serverless platform for containerized applications.
*   **Secret Manager:** Secrets are handled using **Google Cloud secret manager**.

#### Software Development Lifecycle (SDLC)

The project employs a robust CI/CD pipeline managed by GitHub Actions to ensure code quality, automated testing, and seamless deployment across development, staging, and production environments.

*   **`ci.yml` (Continuous Integration):**
    *   Triggered on `push` and `pull_request` to `main` and `develop` branches.
    *   Runs unit tests for both backend (Python `pytest`) and frontend (Node.js `Vitest`).
    *   Enforces code formatting standards using `black` for Python and `prettier` for TypeScript/JavaScript.
    *   Ensures code quality and catches issues early in the development cycle.
*   **`backend_cd.yml` (Backend Continuous Deployment):**
    *   Triggered on `push` to the `main` branch or via `workflow_dispatch` (manual trigger).
    *   Authenticates with Google Cloud using **Workload Identity Federation**.
    *   Builds the FastAPI backend Docker image.
    *   Pushes the Docker image to **Google Artifact Registry**.
    *   Deploys the containerized backend to **Google Cloud Run**, exposing it as a service.
    *   Secrets (e.g., `DATABASE_URL`, `GOOGLE_APPLICATION_CREDENTIALS`, `GOOGLE_API_KEY`) are securely managed and passed to Cloud Run.
*   **`frontend_cd.yml` (Frontend Continuous Deployment):**
    *   Triggered on `push` to the `main` branch or via `workflow_dispatch`.
    *   Similar to the backend CD, it authenticates with Google Cloud.
    *   Builds the React frontend Docker image (using Nginx to serve static files).
    *   Pushes the Docker image to **Google Artifact Registry**.
    *   Deploys the containerized frontend to **Google Cloud Run**.

This setup ensures that any changes merged into the `main` branch are automatically built, tested, and deployed.

### AI Disclosure

The FinOps Intelligence Dashboard extensively utilizes Artificial Intelligence, specifically **Google Generative AI (Gemini Model)**, to transform raw cloud cost data into actionable insights.

*   **Role of AI within the Application:**
    *   **Backend Integration (`backend/app/services/llm.py`):** The backend service acts as an intermediary, securely sending aggregated FinOps data to the Gemini model and processing its responses. It uses the Gemini model to:
        *   Generate natural language summaries of cloud spend.
        *   Detect unusual spending patterns and anomalies.
        *   Provide predictive forecasting for future costs.
        *   Offer concrete cost optimization recommendations.
        *   Answer natural language queries about cloud costs.
    *   **Frontend Interaction (`frontend/src/components/AIInsightPanel.tsx`):** The dashboard provides a dedicated "AI-Powered FinOps Insights" panel where users can:
        *   Select different types of insights (e.g., summary, anomaly, recommendation, natural query).
        *   Input natural language questions related to their cloud spend.
        *   Receive AI-generated responses directly within the application, often contextualized by the currently applied dashboard filters (project, service, SKU, date ranges).

*   **AI Tools Used for Development:**
    *   This project's documentation and some aspects of its structure were assisted by a **Gemini CLI agent**. The agent's role was to analyze the existing codebase, understand its architecture, and synthesize detailed explanations and setup instructions.

### Engineering Roadmap

To evolve the FinOps Intelligence Dashboard to handle massive data volumes or stricter compliance requirements, the following areas will be prioritized:

#### 1. Scalability for Massive Data Volumes

*   **Database Scaling (PostgreSQL):**
    *   **Read Replicas:** Implement read replicas for Cloud SQL to distribute read loads, improving frontend responsiveness for data-intensive queries.
    *   **Database Sharding/Partitioning:** For exceptionally high write and read throughput requirements on the operational database, explore sharding or advanced table partitioning strategies.
*   **BigQuery Optimization:**
    *   **Clustering & Partitioning:** Continuously review and optimize BigQuery table schemas for optimal query performance and cost efficiency, ensuring proper clustering and partitioning keys are applied.
    *   **Materialized Views:** Leverage BigQuery Materialized Views for frequently accessed, pre-aggregated datasets to reduce query latency and costs.
    *   **Streaming Inserts:** For real-time billing data ingestion, integrate BigQuery streaming inserts to provide near real-time insights.
*   **Caching Layer:**
    *   **Distributed Cache:** Introduce a distributed caching solution (e.g., **Redis** via **Google Cloud Memorystore**) for frequently accessed but slow-changing data, such as distinct service/project/SKU lists, or popular AI insight responses.
*   **Batch Processing:** For very large-scale data transformations, aggregations, or machine learning model training that are not time-sensitive, consider dedicated batch processing solutions.
