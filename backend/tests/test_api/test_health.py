"""Tests for health check API endpoint."""

import pytest
from fastapi.testclient import TestClient


def test_healthcheck_returns_200(client: TestClient):
    """Test that health check endpoint returns 200 with correct structure."""
    response = client.get("/api/health")
    
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert data["status"] in ["ok", "degraded"]
    assert "timestamp" in data
    assert "version" in data
    assert data["version"] == "1.0.0"


def test_healthcheck_response_format(client: TestClient):
    """Test that health check response has the expected format."""
    response = client.get("/api/health")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    
    data = response.json()
    
    # Check required fields
    required_fields = ["status", "timestamp", "version"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    # Check data types
    assert isinstance(data["status"], str)
    assert isinstance(data["timestamp"], str)
    assert isinstance(data["version"], str)
