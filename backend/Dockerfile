# Dockerfile for the FastAPI FinOps Intelligence Dashboard Backend

# Use a lightweight Python base image
# Python 3.11 is chosen for its balance of features and stability,
# ensuring compatibility with FastAPI and other libraries.
FROM python:3.11-slim-buster

# Set the working directory inside the container
# All subsequent commands will be executed relative to this directory.
WORKDIR /app

# Copy the requirements file into the container
# This step is done separately to leverage Docker's layer caching.
# If only requirements.txt changes, this layer and subsequent layers are rebuilt.
COPY requirements.txt .

# Install Python dependencies
# `pip install --no-cache-dir` reduces the size of the Docker image by
# not storing cached pip packages.
# `setuptools` is included as a common dependency for many Python packages.
RUN pip install --no-cache-dir -r requirements.txt setuptools

# Copy the rest of the application code into the container
# The '.' at the end copies everything from the current host directory (backend/)
# into the WORKDIR (/app) in the container.
COPY . .

# Expose the port on which the FastAPI application will run
# This informs Docker that the container listens on the specified network ports
# at runtime.
EXPOSE 8000

# Set environment variables for non-root user and production settings
# These are best practices for security and performance in Docker containers.
# `PYTHONUNBUFFERED=1` ensures Python output is not buffered, making logs
# immediately visible in container logs.
# `POETRY_VIRTUALENVS_CREATE=false` (if poetry was used) prevents creating
# an internal venv in CI/Docker build, as we already have one or want global install.
ENV PYTHONUNBUFFERED=1

# Command to run the FastAPI application using Uvicorn
# `uvicorn app.main:app` specifies the application entry point.
# `--host 0.0.0.0` makes the server accessible from outside the container.
# `--port 8000` specifies the port.
# `--workers 4` (or number of CPU cores) is good for production to handle multiple requests.
# `--log-level info` sets the logging level.
# In a production environment, `--reload` should NOT be used.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--log-level", "info"]
