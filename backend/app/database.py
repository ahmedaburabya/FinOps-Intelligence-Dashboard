from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Removed: from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv
from typing import Optional

# Import the Base from models.py where it is now defined
from app.models import Base  # Ensure all models are registered with this Base

# Load environment variables from .env file
load_dotenv()

# --- Database Configuration ---
# Retrieve database connection details from environment variables.
# This ensures that sensitive information is not hardcoded and allows for
# easy configuration across different environments (development, staging, production).
# Example .env entries:
# DATABASE_URL="postgresql://user:password@host:port/dbname"
# SQLALCHEMY_ECHO=False (set to True to log all SQL statements)
DATABASE_URL = os.getenv("DATABASE_URL")
SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true"

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is not set. Please provide a PostgreSQL connection string."
    )

# --- SQLAlchemy Engine Creation ---
# The engine is the starting point for any SQLAlchemy application. It's responsible
# for communicating with the database.
# `pool_pre_ping=True` ensures that connections in the pool are still alive.
# `echo=SQLALCHEMY_ECHO` will log all SQL statements to stdout if enabled.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=SQLALCHEMY_ECHO)

# --- Session Local (Session Factory) ---
# `sessionmaker` creates a class that will act as a factory for `Session` objects.
# Each `Session` is a transactional unit for managing database interactions.
# `autocommit=False` means changes are not committed automatically.
# `autoflush=False` means changes are not flushed to the database until commit or explicit flush.
# `bind=engine` associates this session factory with our database engine.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Base for Declarative Models ---
# Base is now imported from app.models, where it is defined.
# Removed: Base = declarative_base()


# --- Utility Function to Create All Tables ---
def init_db(db_url: Optional[str] = None):
    """
    Creates all defined database tables in the database associated with the engine.
    This is typically used for initial setup or in development environments.
    In production, Alembic migrations are preferred for schema management.
    """
    # Use the provided db_url if available, otherwise fall back to the environment variable
    effective_db_url = db_url if db_url else DATABASE_URL
    if not effective_db_url:
        raise ValueError("DATABASE_URL is not set and no db_url provided to init_db.")

    # Create a temporary engine for this operation, ensuring we use the correct URL
    temp_engine = create_engine(
        effective_db_url, pool_pre_ping=True, echo=SQLALCHEMY_ECHO
    )

    print(
        f"Attempting to connect to database at: {effective_db_url.split('@')[-1] if '@' in effective_db_url else effective_db_url}"
    )
    try:
        # Import all models to ensure they are registered with the Base metadata
        # This is implicitly handled by 'from app.models import Base' at the top,
        # as importing Base also executes the models.py module where models are defined.
        print(
            f"Tables known to SQLAlchemy Base.metadata: {Base.metadata.tables.keys()}"
        )
        Base.metadata.create_all(bind=temp_engine)
        print("Database tables created successfully (if they didn't exist).")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise


# --- Dependency to Get DB Session ---
def get_db():
    """
    Dependency function to provide a database session to FastAPI endpoints.
    This ensures that each request gets its own session, and the session is
    properly closed after the request is processed, even if errors occur.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    # Example usage: Initialize the database when this script is run directly
    print("Running database initialization directly...")
    init_db()
