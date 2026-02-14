# FinOps Intelligence Dashboard Backend

This repository contains the backend for the FinOps Intelligence Dashboard, a tool designed to transform raw cloud spend data from Google Cloud BigQuery into actionable business insights using AI.

## Table of Contents

- [Project Objective](#project-objective)
- [Technical Stack](#technical-stack)
- [Setup and Local Execution](#setup-and-local-execution)
- [API Endpoints](#api-endpoints)
- [Architecture & SDLC Overview](#architecture--sdlc-overview)
- [AI Disclosure](#ai-disclosure)
- [Engineering Roadmap](#engineering-roadmap)
- [Frontend Implementation](#frontend-implementation)

## Project Objective

The primary objective is to design, develop, and deploy a production-grade FinOps Intelligence Tool. This application interfaces with a live Google Cloud BigQuery billing dataset to aggregate raw cloud spend and generate AI-driven insights for cost optimization and anomaly detection.

## Technical Stack

*   **Backend**: Python 3.9+ with FastAPI
*   **Database**: PostgreSQL (managed via SQLAlchemy and Alembic)
*   **Data Source**: Google Cloud BigQuery billing export
*   **AI/LLM**: Google Generative AI (Gemini Model)
*   **Dependency Management**: Poetry
*   **Containerization**: Docker & Docker Compose
*   **Frontend**: React with TypeScript and Material UI (MUI)

## Setup and Local Execution

This section details how to set up the development environment and run the backend locally.

### Prerequisites:

1.  **Python 3.9+**: Ensure Python is installed on your system.
2.  **Poetry**: The project uses Poetry for dependency management. Install it via `pip install poetry`.
3.  **Node.js & npm/yarn**: Required for frontend development.
4.  **Docker & Docker Compose**: Required for running the application in a containerized environment (recommended).
5.  **Google Cloud Project**: An active Google Cloud Project with BigQuery enabled.
6.  **Google Service Account Key**: A JSON key file for a Google Service Account with at least the following roles:
    *   `BigQuery Data Viewer`
    *   `BigQuery Job User`
    *   (If you plan to ingest data) `BigQuery Data Editor`
7.  **Google Generative AI API Key**: An API key for accessing the Gemini model.

### Setup Steps:

1.  **Clone the Repository (if not already done):**
    ```bash
    git clone https://github.com/your-repo/FinOpsIntelligenceDashboard.git # Replace with actual repo URL
    cd FinOpsIntelligenceDashboard/Backend
    ```

2.  **Install Backend Python Dependencies:**
    Navigate to the `backend` directory:
    ```bash
    cd backend
    poetry install
    ```

3.  **Install Frontend Node.js Dependencies:**
    Navigate to the `frontend` directory:
    ```bash
    cd ../frontend
    npm install
    # or yarn install if you prefer yarn
    ```

4.  **Environment Variables Configuration:**
    Create a `.env` file in the `backend` directory (e.g., `FinOpsIntelligenceDashboard/Backend/backend/.env`) with the following variables. **Replace placeholder values with your actual credentials and details.**

    ```dotenv
    # Google Cloud BigQuery Service Account
    # Path to your Google Cloud service account key JSON file.
    # For local development, place it in the 'backend/' directory.
    GOOGLE_APPLICATION_CREDENTIALS=./service-account-file.json
    
    # Google Generative AI (Gemini) API Key
    # Obtain this from Google AI Studio or Google Cloud Console
    GOOGLE_API_KEY=YOUR_GOOGLE_GENERATIVE_AI_API_KEY
    
    # Optional: Specify the LLM model name if different from default (gemini-2.5-flash)
    # LLM_MODEL_NAME=gemini-1.5-pro-latest
    
    # Database Configuration (for PostgreSQL via SQLAlchemy)
    # This URL is used by the FastAPI app to connect to the PostgreSQL database.
    # When running with Docker Compose, 'db' is the service name of the PostgreSQL container.
    DATABASE_URL="postgresql+psycopg2://user:password@db:5432/finops_db"
    
    # For local testing without Docker, if you have a local PostgreSQL instance:
    # DATABASE_URL="postgresql+psycopg2://user:password@localhost:5432/finops_db"

    # BigQuery Specifics (Adjust as per your BigQuery billing export setup)
    # The dataset and table where your GCP billing export data resides.
    # You'll need to specify these parameters when calling the BigQuery ingestion endpoint.
    # Example:
    # BIGQUERY_BILLING_DATASET_ID="my_billing_dataset"
    # BIGQUERY_BILLING_TABLE_ID="gcp_billing_export_resource_v1_XXXXXX"

    # GCP Project ID (Optional, but good practice for clarity and future use)
    # GCP_PROJECT_ID="your-gcp-project-id"
    ```
    For the frontend, create `.env.development` and `.env.production` in the `frontend/` directory (i.e., `FinOpsIntelligenceDashboard/Backend/frontend/.env.development`).

    **`frontend/.env.development`**:
    ```dotenv
    VITE_API_BASE_URL=http://localhost:8000/api/v1
    ```
    **`frontend/.env.production`**:
    ```dotenv
    # In a production Docker environment, Nginx will handle proxying
    # This value might be empty or point to a relative path handled by Nginx.
    # The Dockerfile handles setting this via build args if needed.
    VITE_API_BASE_URL=/api/v1 
    ```

5.  **Place Service Account Key File:**
    Move your downloaded Google Service Account JSON key file into the `backend/` directory (i.e., `FinOpsIntelligenceDashboard/Backend/backend/`). Rename it to `service-account-file.json` if it has a different name. Ensure the `GOOGLE_APPLICATION_CREDENTIALS` variable in your `.env` file points to this file correctly.

### Running the Application:

#### Using Docker Compose (Recommended for Development and Production):

This method sets up the FastAPI application, a PostgreSQL database, and the Nginx-served React frontend.

1.  **Configure `docker-compose.yml`**:
    Ensure your `docker-compose.yml` (at `FinOpsIntelligenceDashboard/Backend/docker-compose.yml`) includes the frontend service.
    
    ```yaml
    # Example docker-compose.yml (ensure it's updated in your project root)
    version: '3.8'

    services:
      db:
        image: postgres:16-alpine
        volumes:
          - postgres_data:/var/lib/postgresql/data/
        environment:
          POSTGRES_DB: finops_db
          POSTGRES_USER: user
          POSTGRES_PASSWORD: password
        ports:
          - "5432:5432" # Expose for local debugging if needed
        healthcheck:
          test: ["CMD-SHELL", "pg_isready -U user -d finops_db"]
          interval: 5s
          timeout: 5s
          retries: 5

      backend:
        build:
          context: ./backend
          dockerfile: Dockerfile
        depends_on:
          db:
            condition: service_healthy
        environment:
          # Ensure these match your .env in backend directory or are passed here
          GOOGLE_APPLICATION_CREDENTIALS: /app/service-account-file.json
          GOOGLE_API_KEY: ${GOOGLE_API_KEY} # Passed from host env
          DATABASE_URL: postgresql+psycopg2://user:password@db:5432/finops_db
        volumes:
          - ./backend/service-account-file.json:/app/service-account-file.json:ro
          # Mount the backend source code for live reload during development (optional)
          # - ./backend/app:/app/app 
        ports:
          - "8000:8000"
        command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
        # For development with live reload:
        # command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

      frontend:
        build:
          context: ./frontend
          dockerfile: Dockerfile
          args:
            VITE_API_BASE_URL: /api/v1 # Nginx will proxy this to backend service
        ports:
          - "5173:80" # Expose frontend on port 5173
        depends_on:
          - backend
        volumes:
          # Mount frontend source code for development (optional, not used in multi-stage build directly)
          # - ./frontend:/app
          # - /app/node_modules # Anonymous volume to prevent host node_modules from overriding container
    
    volumes:
      postgres_data:
    ```

2.  **Build and Run**:
    Navigate to the project root (`FinOpsIntelligenceDashboard/Backend`).
    ```bash
    docker compose up --build
    ```
    This command will:
    *   Build Docker images for the backend and frontend.
    *   Start the PostgreSQL database.
    *   Start the FastAPI backend application.
    *   Start the Nginx server serving the React frontend.

    The backend API will be accessible at `http://localhost:8000`.
    The frontend application will be accessible at `http://localhost:5173`.
    Explore interactive API documentation at `http://localhost:8000/docs`.

#### Running Backend Locally (without Docker Compose for Backend):

If you prefer to run the FastAPI application directly (assuming you have a local PostgreSQL running and configured as per `DATABASE_URL` in `.env`):

Navigate to the `backend` directory.
```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The `--reload` flag is useful for development as it automatically restarts the server on code changes.

#### Running Frontend Locally (without Docker Compose for Frontend):

1.  **Start the Backend**: Ensure your backend API is running, either via Docker Compose or locally (`http://localhost:8000`).
2.  **Navigate to Frontend Directory**:
    ```bash
    cd frontend
    ```
3.  **Start Development Server**:
    ```bash
    npm run dev
    # or yarn dev
    ```
    The frontend application will typically be accessible at `http://localhost:5173`. It will automatically proxy API calls to `http://localhost:8000/api/v1` as configured in `frontend/.env.development`.

## API Endpoints

The API provides endpoints for managing aggregated cost data, interacting with BigQuery, and leveraging LLM-generated insights. The full interactive documentation is available at `/docs` when the server is running.

**Key Endpoint Categories:**

*   **`/api/v1/finops/aggregated-cost`**: CRUD operations for aggregated cost data stored in the local PostgreSQL database.
*   **`/api/v1/finops/overview`**: High-level FinOps metrics (MTD Spend, Burn Rate).
*   **`/api/v1/finops/bigquery/...`**: Endpoints for exploring BigQuery datasets/tables and ingesting billing data.
*   **`/api/v1/finops/generate-spend-summary`**: Triggers LLM to generate a spend summary.
*   **`/api/v1/finops/llm-insight`**: CRUD for LLM-generated insights.

## Architecture & SDLC Overview

### Architecture:

The backend follows a layered architectural pattern, promoting separation of concerns and maintainability:

1.  **API Layer (`app/api/v1/endpoints`):** Exposes RESTful endpoints using FastAPI. Handles request parsing, validation (via Pydantic schemas), and delegates business logic to services.
2.  **Service Layer (`app/services`):** Contains core business logic and integrations with external systems.
    *   `bigquery.py`: Handles authentication, querying, and data retrieval from Google Cloud BigQuery.
    *   `llm.py`: Integrates with Google Generative AI for generating AI-driven insights.
3.  **CRUD Layer (`app/crud.py`):** Provides an abstraction over database operations, interacting directly with SQLAlchemy models.
4.  **Database Layer (`app/database.py`, `app/models.py`):**
    *   `app/database.py`: Manages database session creation and initialization (via SQLAlchemy).
    *   `app/models.py`: Defines the SQLAlchemy ORM models, mapping Python objects to database tables.
5.  **Schemas Layer (`app/schemas.py`):** Defines Pydantic models for data validation, serialization, and API documentation.

The frontend is a single-page application (SPA) built with:
*   **React**: For building interactive user interfaces.
*   **TypeScript**: For type safety and improved code quality.
*   **Material UI (MUI)**: A comprehensive React UI library implementing Google's Material Design.
*   **Vite**: A fast build tool for modern web projects.
*   **React Router DOM**: For declarative routing within the SPA.
*   **Axios**: For making HTTP requests to the backend API.

### SDLC and Environment Strategy:

The solution is designed to support a standard enterprise release cycle with distinct environments:

*   **Development**: Local development setup, where developers write and test code. Utilizes Docker Compose for easy local environment parity.
*   **Staging**: An environment that mirrors production as closely as possible, used for integration testing, quality assurance, and user acceptance testing before production deployment.
*   **Production**: The live environment serving end-users.

**Key Principles:**

*   **Environment Isolation**: Achieved through separate environment configurations (e.g., `.env` files, Kubernetes ConfigMaps/Secrets) for each tier, ensuring that changes in one environment do not impact others. Docker images are built once and promoted across environments.
*   **Secrets Management**: Sensitive information (API keys, service account credentials, database passwords) are managed securely. Locally, `.env` files are used and excluded from version control (`.gitignore`). In production, Kubernetes Secrets, Google Secret Manager, or similar secure solutions would be employed.
*   **Promotion Workflow**: Code changes flow from development -> staging -> production. This typically involves:
    1.  Feature development on branches.
    2.  Code review and merging into `main`/`develop`.
    3.  Automated CI/CD pipelines building Docker images and deploying to staging.
    4.  Manual or automated testing in staging.
    5.  Promotion to production, often triggered manually after successful staging tests, deploying the *same* Docker image built earlier.
*   **Production Standards**:
    *   **Structured Logging**: All services use Python's `logging` module with structured formats (e.g., JSON) for easier analysis in centralized logging systems.
    *   **Error Handling**: Comprehensive error handling using FastAPI's `HTTPException` and custom exception handlers where appropriate, providing clear error messages without exposing sensitive details. On the frontend, global `SnackbarAlert` and localized error messages provide user feedback.
    *   **Performance Optimization**:
        *   **BigQuery**: Efficient SQL queries, leveraging partitioning and clustering where applicable.
        *   **Database**: SQLAlchemy's ORM used efficiently, with bulk inserts for ingestion (`bulk_create_aggregated_cost_data`).
        *   **Asynchronous Processing**: Non-blocking BigQuery and LLM calls using `asyncio.run_in_executor` to maintain API responsiveness.
        *   **Caching**: (Future enhancement) Caching frequently accessed FinOps data to reduce database/BigQuery load.

## AI Disclosure

This application leverages Google Generative AI (specifically the Gemini family of models) to provide enhanced FinOps insights.

*   **Tool Used**: `google.generativeai` Python SDK.
*   **Role within the Application**:
    *   **Spend Summarization**: The LLM analyzes aggregated cloud cost data to generate natural language summaries of spending trends, helping users quickly grasp key financial movements.
    *   **Anomaly Detection**: By processing historical and recent cost data, the LLM can identify unusual spending patterns or spikes that might indicate unexpected usage, misconfigurations, or potential waste.
    *   **Cost Optimization Recommendations**: Based on the analyzed data, the LLM can suggest actionable recommendations for optimizing cloud spend, such as identifying underutilized resources, recommending different service tiers, or highlighting potential areas for policy enforcement.
*   **Data Handling**: Only aggregated and non-personally identifiable cost data is sent to the LLM. No sensitive or raw billing details are transmitted. Input data is also truncated if it exceeds a predefined character limit to manage context window and cost.
*   **Ethical Considerations**: The AI's outputs are intended as insights and recommendations, not definitive financial advice. Users should use their judgment and domain expertise to validate and act upon these suggestions. Continuous monitoring of AI performance and bias is crucial.

## Engineering Roadmap

This section outlines potential future enhancements and architectural evolutions.

### Short-Term (0-3 Months):

*   **Enhanced LLM Features**:
    *   Implement interactive chat for FinOps questions.
    *   More sophisticated anomaly detection algorithms (e.g., integration with time-series anomaly detection libraries).
    *   Detailed cost allocation breakdowns based on AI analysis.
*   **Frontend Development**: Implement a comprehensive web UI for data visualization and interaction with AI insights.
*   **Alerting**: Integrate with notification systems (e.g., Slack, PagerDuty) for AI-detected anomalies or critical spending thresholds.
*   **More Granular Aggregation**: Support for hourly aggregation, custom tags, and labels from BigQuery.

### Mid-Term (3-12 Months):

*   **Multi-Cloud Support**: Extend BigQuery integration to support billing data from other cloud providers (AWS Cost and Usage Report, Azure Cost Management). This would involve abstracting the data ingestion layer.
*   **Advanced Cost Optimization**:
    *   Integration with cloud provider APIs for automated resource rightsizing or shutdown recommendations.
    *   Forecasting future spend based on historical trends and AI models.
*   **Performance Scaling**:
    *   Implement Redis for API caching to reduce database and BigQuery query load.
    *   Explore distributed task queues (e.g., Celery with RabbitMQ) for long-running BigQuery ingestion or complex LLM analysis tasks.
*   **Reporting**: Generate scheduled PDF/CSV reports based on FinOps insights.

### Long-Term (12+ Months):

*   **Massive Data Volumes / Data Lake Integration**:
    *   Transition from direct BigQuery queries to a data lake architecture (e.g., Apache Hudi, Delta Lake) on Google Cloud Storage for enhanced flexibility, versioning, and analytics at scale.
    *   Utilize BigQuery ML or Vertex AI Workbench for advanced custom ML models for forecasting, anomaly detection, and optimization, moving beyond purely Generative AI for specific tasks.
*   **Stricter Compliance Requirements**:
    *   Implement robust audit logging and access control at a granular level.
    *   Data residency controls and encryption at rest/in transit across all components.
    *   Formal security assessments and penetration testing.
*   **User Management & RBAC**: Implement comprehensive user authentication and role-based access control (RBAC) for different levels of FinOps users.
*   **Self-Healing Infrastructure**: Automate environment provisioning and healing using Infrastructure as Code (IaC) tools and robust monitoring.
