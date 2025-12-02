"""Tests for product endpoints."""
import pytest
from fastapi import status


def test_get_all_products_endpoint(client):
    """Test getting all products endpoint."""
    response = client.get("/api/products/hunnit")
    # Should return 200 even if no products (empty list)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)


def test_get_product_count_endpoint(client):
    """Test product count endpoint."""
    response = client.get("/api/products/hunnit/stats/count")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "count" in data
    assert isinstance(data["count"], int)
    assert "source" in data


def test_get_cache_status_endpoint(client):
    """Test cache status endpoint."""
    response = client.get("/api/products/hunnit/cache/status")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "cache_available" in data
    assert "status" in data


def test_get_product_by_id_not_found(client):
    """Test getting non-existent product returns 404."""
    response = client.get("/api/products/hunnit/non-existent-id")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "detail" in data

