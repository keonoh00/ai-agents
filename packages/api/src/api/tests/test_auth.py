"""
Tests for authentication.
"""
import os

import pytest


def test_auth_with_valid_key(client, api_key):
    """Test authentication with valid API key."""
    headers = {"Authorization": f"Bearer {api_key}"}
    response = client.get("/v1/models", headers=headers)
    assert response.status_code == 200


def test_auth_with_invalid_key(client):
    """Test authentication with invalid API key."""
    headers = {"Authorization": "Bearer invalid-key"}
    response = client.get("/v1/models", headers=headers)
    assert response.status_code == 401


def test_auth_without_key(client):
    """Test that endpoints require authentication."""
    response = client.get("/v1/models")
    assert response.status_code == 401


def test_auth_with_wrong_format(client):
    """Test authentication with wrong header format."""
    # Missing "Bearer " prefix
    headers = {"Authorization": "test-api-key"}
    response = client.get("/v1/models", headers=headers)
    assert response.status_code == 401


def test_health_endpoint_no_auth(client):
    """Test that health endpoint doesn't require auth."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_root_endpoint_no_auth(client):
    """Test that root endpoint doesn't require auth."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

