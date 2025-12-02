"""Tests for health check endpoints."""
import pytest
from fastapi import status


def test_root_endpoint(client):
    """Test root endpoint returns hello message."""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert isinstance(data["message"], str)


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "unhealthy"]

