"""
Tests for /v1/embeddings endpoint.
"""
from unittest.mock import patch

import pytest


def test_embeddings_single_text(client, headers, mock_embedding_model):
    """Test embeddings with single text input."""
    with patch("api.models.embedding.get_embedding_model", return_value=mock_embedding_model):
        response = client.post(
            "/v1/embeddings",
            headers=headers,
            json={
                "model": "local-embedding",
                "input": "The quick brown fox jumps over the lazy dog",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "object" in data
        assert data["object"] == "list"
        assert "data" in data
        assert len(data["data"]) == 1
        assert "embedding" in data["data"][0]
        assert isinstance(data["data"][0]["embedding"], list)
        assert len(data["data"][0]["embedding"]) > 0
        assert "usage" in data
        assert "prompt_tokens" in data["usage"]


def test_embeddings_multiple_texts(client, headers, mock_embedding_model):
    """Test embeddings with multiple text inputs."""
    with patch("api.models.embedding.get_embedding_model", return_value=mock_embedding_model):
        response = client.post(
            "/v1/embeddings",
            headers=headers,
            json={
                "model": "local-embedding",
                "input": [
                    "First text",
                    "Second text",
                    "Third text",
                ],
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 3
        for i, item in enumerate(data["data"]):
            assert item["index"] == i
            assert "embedding" in item


def test_embeddings_no_auth(client):
    """Test that embeddings requires authentication."""
    response = client.post(
        "/v1/embeddings",
        json={
            "model": "local-embedding",
            "input": "test",
        },
    )
    assert response.status_code == 401


def test_embeddings_invalid_request(client, headers):
    """Test embeddings with invalid request."""
    # Missing input
    response = client.post(
        "/v1/embeddings",
        headers=headers,
        json={"model": "local-embedding"},
    )
    assert response.status_code == 422  # Validation error


def test_embeddings_empty_input(client, headers, mock_embedding_model):
    """Test embeddings with empty input."""
    with patch("api.models.embedding.get_embedding_model", return_value=mock_embedding_model):
        response = client.post(
            "/v1/embeddings",
            headers=headers,
            json={
                "model": "local-embedding",
                "input": "",
            },
        )
        
        # Should still return 200 but with empty embedding
        assert response.status_code == 200

