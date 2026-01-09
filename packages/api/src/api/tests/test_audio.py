"""
Tests for /v1/audio/speech endpoint.
"""

from unittest.mock import patch

import pytest


def test_audio_speech_basic(client, headers, mock_tts_model):
    """Test basic text-to-speech generation."""
    with patch("api.models.tts_model.edge_tts") as mock_edge_tts, patch(
        "api.models.tts_model._convert_audio_with_ffmpeg", return_value=b"converted-wav"
    ):
        mock_edge_tts.Communicate = mock_tts_model
        response = client.post(
            "/v1/audio/speech",
            headers=headers,
            json={
                "model": "local-tts",
                "input": "Hello, this is a test.",
                "voice": "default",
                "format": "wav",
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"
        assert len(response.content) > 0


def test_audio_speech_different_formats(client, headers, mock_tts_model):
    """Test text-to-speech with different audio formats."""
    formats = ["wav", "mp3", "opus", "flac"]

    with patch("api.models.tts_model.edge_tts") as mock_edge_tts, patch(
        "api.models.tts_model._convert_audio_with_ffmpeg", return_value=b"converted"
    ):
        mock_edge_tts.Communicate = mock_tts_model
        for audio_format in formats:
            response = client.post(
                "/v1/audio/speech",
                headers=headers,
                json={
                    "model": "local-tts",
                    "input": "Test audio",
                    "format": audio_format,
                },
            )

            assert response.status_code == 200
            assert len(response.content) > 0


def test_audio_speech_different_voices(client, headers, mock_tts_model):
    """Test text-to-speech with different voices."""
    voices = ["default", "alloy", "echo", "fable"]

    with patch("api.models.tts_model.edge_tts") as mock_edge_tts, patch(
        "api.models.tts_model._convert_audio_with_ffmpeg", return_value=b"converted"
    ):
        mock_edge_tts.Communicate = mock_tts_model
        for voice in voices:
            response = client.post(
                "/v1/audio/speech",
                headers=headers,
                json={
                    "model": "local-tts",
                    "input": "Test audio",
                    "voice": voice,
                },
            )

            assert response.status_code == 200
            assert len(response.content) > 0


def test_audio_speech_no_auth(client):
    """Test that audio speech requires authentication."""
    response = client.post(
        "/v1/audio/speech",
        json={
            "model": "local-tts",
            "input": "Test",
        },
    )
    assert response.status_code == 401


def test_audio_speech_invalid_request(client, headers):
    """Test audio speech with invalid request."""
    # Missing input
    response = client.post(
        "/v1/audio/speech",
        headers=headers,
        json={"model": "local-tts"},
    )
    assert response.status_code == 422  # Validation error


def test_audio_speech_empty_input(client, headers, mock_tts_model):
    """Test audio speech with empty input."""
    with patch("api.models.tts_model.edge_tts") as mock_edge_tts, patch(
        "api.models.tts_model._convert_audio_with_ffmpeg", return_value=b"converted"
    ):
        mock_edge_tts.Communicate = mock_tts_model
        response = client.post(
            "/v1/audio/speech",
            headers=headers,
            json={
                "model": "local-tts",
                "input": "",
            },
        )

        # Should still return 200 but with minimal audio
        assert response.status_code == 200
