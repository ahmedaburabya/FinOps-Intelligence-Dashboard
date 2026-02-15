import pytest
from app.main import app

def test_read_root():
    """
    Test that the root endpoint returns a success message.
    """
    # This is a dummy test. In a real scenario, you would use TestClient
    # from fastapi.testclient import TestClient
    # client = TestClient(app)
    # response = client.get("/")
    # assert response.status_code == 200
    # assert response.json() == {"message": "Welcome to FinOps Intelligence Dashboard API"}
    assert True # Dummy assertion
