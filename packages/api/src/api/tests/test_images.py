"""
Tests for /v1/images/generations endpoint.
"""
import base64
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image


def test_image_generation_basic(client, headers, mock_image_pipeline):
    """Test basic image generation."""
    # Fix the mock to return proper structure
    mock_pipeline = MagicMock()
    mock_image = Image.new("RGB", (512, 512), color="red")
    mock_result = MagicMock()
    mock_result.images = [mock_image]
    mock_pipeline.return_value = mock_result
    
    with patch("api.models.image_model.get_image_model", return_value=mock_pipeline):
        response = client.post(
            "/v1/images/generations",
            headers=headers,
            json={
                "model": "local-image",
                "prompt": "A beautiful sunset over the ocean",
                "size": "512x512",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "created" in data
        assert "data" in data
        assert len(data["data"]) > 0
        assert "b64_json" in data["data"][0]
        
        # Verify it's valid base64
        b64_data = data["data"][0]["b64_json"]
        decoded = base64.b64decode(b64_data)
        assert len(decoded) > 0


def test_image_generation_different_sizes(client, headers, mock_image_pipeline):
    """Test image generation with different sizes."""
    sizes = ["256x256", "512x512", "1024x1024"]
    
    # Fix the mock
    mock_pipeline = MagicMock()
    mock_image = Image.new("RGB", (512, 512), color="red")
    mock_result = MagicMock()
    mock_result.images = [mock_image]
    mock_pipeline.return_value = mock_result
    
    with patch("api.models.image_model.get_image_model", return_value=mock_pipeline):
        for size in sizes:
            response = client.post(
                "/v1/images/generations",
                headers=headers,
                json={
                    "model": "local-image",
                    "prompt": "A test image",
                    "size": size,
                },
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "data" in data


def test_image_generation_invalid_size(client, headers, mock_image_pipeline):
    """Test image generation with invalid size format."""
    # Fix the mock
    mock_pipeline = MagicMock()
    mock_image = Image.new("RGB", (512, 512), color="red")
    mock_result = MagicMock()
    mock_result.images = [mock_image]
    mock_pipeline.return_value = mock_result
    
    with patch("api.models.image_model.get_image_model", return_value=mock_pipeline):
        response = client.post(
            "/v1/images/generations",
            headers=headers,
            json={
                "model": "local-image",
                "prompt": "A test image",
                "size": "invalid",
            },
        )
        
        # Should still work, using default size
        assert response.status_code == 200


def test_image_generation_no_auth(client):
    """Test that image generation requires authentication."""
    response = client.post(
        "/v1/images/generations",
        json={
            "model": "local-image",
            "prompt": "A test image",
        },
    )
    assert response.status_code == 401


def test_image_generation_invalid_request(client, headers):
    """Test image generation with invalid request."""
    # Missing prompt
    response = client.post(
        "/v1/images/generations",
        headers=headers,
        json={"model": "local-image"},
    )
    assert response.status_code == 422  # Validation error

