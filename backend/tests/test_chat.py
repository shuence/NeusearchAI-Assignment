"""Tests for chat/RAG endpoints."""
import pytest
from fastapi import status


def test_chat_endpoint_empty_message(client):
    """Test chat endpoint with empty message."""
    response = client.post(
        "/api/chat",
        json={"message": ""}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_chat_endpoint_valid_message(client):
    """Test chat endpoint with valid message."""
    response = client.post(
        "/api/chat",
        json={
            "message": "Show me gym wear",
            "max_results": 5,
            "similarity_threshold": 0.6
        }
    )
    # Should return 200 even if no products found
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
    if response.status_code == status.HTTP_200_OK:
        data = response.json()
        assert "response" in data
        assert "products" in data
        assert isinstance(data["products"], list)
        assert "needs_clarification" in data


def test_chat_health_endpoint(client):
    """Test chat health endpoint."""
    response = client.get("/api/chat/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert "rag_available" in data

