"""
Tests for /v1/models endpoint.
"""

import pytest


def test_list_models(client, headers):
    """Test listing all available models."""
    response = client.get("/v1/models", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "object" in data
    assert data["object"] == "list"
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0

    # Check that each model has required fields
    for model in data["data"]:
        assert "id" in model
        assert isinstance(model["id"], str)


def test_list_models_no_auth(client):
    """Test that listing models requires authentication."""
    response = client.get("/v1/models")
    assert response.status_code == 401


def test_retrieve_model(client, headers):
    """Test retrieving a specific model."""
    # First get list to find a valid model ID
    list_response = client.get("/v1/models", headers=headers)
    assert list_response.status_code == 200
    models = list_response.json()["data"]
    assert len(models) > 0

    model_id = models[0]["id"]

    # Retrieve the specific model
    response = client.get(f"/v1/models/{model_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == model_id
    assert "object" in data


def test_retrieve_model_not_found(client, headers):
    """Test retrieving a non-existent model."""
    response = client.get("/v1/models/non-existent-model", headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert "error" in data


def test_retrieve_model_no_auth(client):
    """Test that retrieving a model requires authentication."""
    response = client.get("/v1/models/local-llm")
    assert response.status_code == 401
