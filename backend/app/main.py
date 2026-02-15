"""
Main FastAPI application entry point.
This module initializes the FastAPI app, includes API routers, and sets up
event handlers for application startup and shutdown.
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # Import CORSMiddleware
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging
from sqlalchemy.orm import Session  # Import Session
from sqlalchemy import text  # Import text for raw SQL

# Import database initialization and session dependency
from app.database import init_db, get_db

# Import BigQuery service
from app.services.bigquery import BigQueryService, bigquery_service

# Import API routers
from app.api.v1.endpoints import finops

# Configure logging for the application
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Asynchronous context manager for managing application startup and shutdown events.
    This function will be executed when the FastAPI application starts and stops.
    """
    logger.info("FastAPI application starting up...")

    # --- Database Initialization ---
    # In a production environment, you would typically rely on Alembic migrations
    # to manage your database schema. However, for initial setup and development,
    # calling init_db() here ensures that tables are created if they don't exist.
    # It's important to note that create_all() does not perform migrations;
    # it only creates tables that don't already exist.
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Depending on the severity, you might want to re-raise or handle gracefully
        # For now, we'll let the application attempt to start, but log the error.

    # --- Other Startup Tasks (e.g., connect to BigQuery, initialize LLM client) ---
    # These services will be initialized and made available through FastAPI's
    # dependency injection system or global singleton patterns as needed.
    # Placeholder for future service initialization.
    try:
        BigQueryService()  # Initialize the BigQueryService singleton
        logger.info("BigQuery service initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize BigQuery service: {e}")
        # Depending on the severity, you might want to re-raise or handle gracefully

    logger.info("Startup complete. Application ready to serve requests.")
    yield  # Application will run until this point

    logger.info("FastAPI application shutting down...")
    # --- Shutdown Tasks (e.g., close database connections, BigQuery clients) ---
    logger.info("Shutdown complete.")


# Initialize the FastAPI application
# The `lifespan` context manager handles startup and shutdown logic.
app = FastAPI(
    title="FinOps Intelligence Dashboard API",
    description="Backend API for multi-dimensional cloud cost aggregation and AI-driven insights.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,  # Assign the lifespan context manager
)

# --- CORS Middleware ---
# Configure CORS to allow requests from the frontend development server.
# In a production environment, you should restrict allow_origins to your frontend's domain.
origins = [
    "https://finops-dashboard-229203399238.europe-west1.run.app",  # Frontend production server
    "http://localhost",
    "http://localhost:5173",  # Frontend development server
    # Add other origins for production, staging, etc.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include API Routers ---
# This organizes endpoints into modular files, improving maintainability.
# All endpoints defined in `finops.py` will be prefixed with `/api/v1/finops`.
app.include_router(finops.router, prefix="/api/v1/finops", tags=["FinOps"])


# --- Root Endpoint (Optional) ---
@app.get("/", summary="Root endpoint for API health check")
async def read_root():
    """
    Returns a simple message to indicate the API is running.
    """
    return {"message": "FinOps Intelligence Dashboard API is running!"}


# --- Health Check Endpoint (More comprehensive than root) ---
@app.get("/health", summary="Detailed health check of the API and its dependencies")
async def health_check(db_session: Session = Depends(get_db)):
    """
    Performs a health check, including database connectivity.
    Raises an HTTPException if the database is unreachable.
    """
    try:
        # Attempt a simple database query to check connectivity
        db_session.execute(text("SELECT 1"))
        return {"status": "ok", "database_connection": "successful"}
    except Exception as e:
        logger.error(f"Health check failed: Database connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")


# Note: BigQuery and LLM service health checks can be added here once those services are integrated.
