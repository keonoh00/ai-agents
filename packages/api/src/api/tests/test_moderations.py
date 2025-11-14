"""
Tests for /v1/moderations endpoint.
"""
from unittest.mock import MagicMock, patch

import pytest
import torch


def test_moderations_single_text(client, headers, mock_moderation_model):
    """Test moderation with single text input."""
    mock_model, mock_tokenizer = mock_moderation_model
    
    with patch("api.routes.moderations.get_moderation_model", return_value=(mock_model, mock_tokenizer)):
        response = client.post(
            "/v1/moderations",
            headers=headers,
            json={
                "model": "local-moderation",
                "input": "This is a test message",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "model" in data
        assert "results" in data
        assert len(data["results"]) > 0
        
        result = data["results"][0]
        assert "flagged" in result
        assert "categories" in result
        assert "category_scores" in result
        
        # Check categories
        categories = result["categories"]
        assert "hate" in categories
        assert "hate/threatening" in categories
        assert "self-harm" in categories
        assert "sexual" in categories
        assert "sexual/minors" in categories
        assert "violence" in categories
        assert "violence/graphic" in categories


def test_moderations_multiple_texts(client, headers, mock_moderation_model):
    """Test moderation with multiple text inputs."""
    mock_model, mock_tokenizer = mock_moderation_model
    
    with patch("api.routes.moderations.get_moderation_model", return_value=(mock_model, mock_tokenizer)):
        response = client.post(
            "/v1/moderations",
            headers=headers,
            json={
                "model": "local-moderation",
                "input": [
                    "First message",
                    "Second message",
                    "Third message",
                ],
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3


def test_moderations_toxic_content(client, headers, mock_moderation_model):
    """Test moderation with potentially toxic content."""
    mock_model, mock_tokenizer = mock_moderation_model
    
    # Mock higher toxic scores
    mock_output = MagicMock()
    mock_output.logits = torch.tensor([[0.8, 0.7, 0.6, 0.5, 0.9, 0.8]])  # High scores
    mock_model.return_value = mock_output
    
    with patch("api.routes.moderations.get_moderation_model", return_value=(mock_model, mock_tokenizer)):
        response = client.post(
            "/v1/moderations",
            headers=headers,
            json={
                "model": "local-moderation",
                "input": "This is a test with potentially toxic content",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        result = data["results"][0]
        # Should be flagged if scores are high enough
        assert isinstance(result["flagged"], bool)


def test_moderations_no_auth(client):
    """Test that moderations requires authentication."""
    response = client.post(
        "/v1/moderations",
        json={
            "model": "local-moderation",
            "input": "test",
        },
    )
    assert response.status_code == 401


def test_moderations_invalid_request(client, headers):
    """Test moderations with invalid request."""
    # Missing input
    response = client.post(
        "/v1/moderations",
        headers=headers,
        json={"model": "local-moderation"},
    )
    assert response.status_code == 422  # Validation error


def test_moderations_empty_input(client, headers, mock_moderation_model):
    """Test moderations with empty input."""
    mock_model, mock_tokenizer = mock_moderation_model
    
    with patch("api.routes.moderations.get_moderation_model", return_value=(mock_model, mock_tokenizer)):
        response = client.post(
            "/v1/moderations",
            headers=headers,
            json={
                "model": "local-moderation",
                "input": "",
            },
        )
        
        # Should still return 200
        assert response.status_code == 200

