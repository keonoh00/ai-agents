"""
Pytest configuration and shared fixtures.
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from api.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def api_key(monkeypatch):
    """Get the test API key from environment or use default."""
    test_key = os.environ.get("OPENAI_API_KEY", "test-api-key")
    # Set the API key in the config for testing
    monkeypatch.setenv("OPENAI_API_KEY", test_key)
    # Also patch the config module
    import api.config

    monkeypatch.setattr(api.config, "MASTER_API_KEY", test_key)
    return test_key


@pytest.fixture
def headers(api_key):
    """Create headers with API key for authenticated requests."""
    return {"Authorization": f"Bearer {api_key}"}


@pytest.fixture
def mock_llm_model():
    """Mock LLM model and tokenizer."""
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()

    # Mock tokenizer.encode to return a tensor-like object
    mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]
    mock_tokenizer.decode.return_value = "This is a test response."
    mock_tokenizer.eos_token_id = 0
    mock_tokenizer.pad_token = None

    # Mock model.generate to return a tensor-like object
    mock_model.generate.return_value = [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]

    return mock_model, mock_tokenizer


@pytest.fixture
def mock_embedding_model():
    """Mock embedding model."""
    mock_model = MagicMock()
    mock_model.encode.return_value = [0.1] * 384  # Return a dummy embedding vector
    mock_model.tokenizer = MagicMock()
    mock_model.tokenizer.encode.return_value = [1, 2, 3, 4]
    return mock_model


@pytest.fixture
def mock_image_pipeline():
    """Mock image generation pipeline."""
    from PIL import Image

    mock_pipeline = MagicMock()
    mock_image = Image.new("RGB", (512, 512), color="red")
    mock_pipeline.return_value.images = [mock_image]
    return mock_pipeline


@pytest.fixture
def mock_tts_model():
    """Mock edge-tts for testing."""
    import wave
    from io import BytesIO

    # Create a minimal WAV file for testing
    buf = BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)  # 16-bit
        w.setframerate(24000)
        # Generate some dummy audio data (silence)
        w.writeframes(b"\x00" * 48000)  # 1 second of silence at 24kHz

    mock_wav_bytes = buf.getvalue()

    # Mock edge_tts.Communicate
    class MockCommunicate:
        def __init__(self, text, voice):
            self.text = text
            self.voice = voice

        async def stream(self):
            # Yield audio chunks
            chunk_size = 1024
            for i in range(0, len(mock_wav_bytes), chunk_size):
                yield {
                    "type": "audio",
                    "data": mock_wav_bytes[i : i + chunk_size],
                }

    return MockCommunicate


@pytest.fixture
def mock_moderation_model():
    """Mock moderation model and tokenizer."""
    import torch

    mock_model = MagicMock()
    mock_tokenizer = MagicMock()

    # Mock tokenizer to return tokenized input
    mock_tokenizer.return_value = {
        "input_ids": torch.tensor([[1, 2, 3, 4]]),
        "attention_mask": torch.tensor([[1, 1, 1, 1]]),
    }

    # Mock model output (6 classes: toxic, severe_toxic, obscene, threat, insult, identity_hate)
    mock_output = MagicMock()
    mock_output.logits = torch.tensor([[0.1, 0.2, 0.3, 0.4, 0.5, 0.6]])
    mock_model.return_value = mock_output

    return mock_model, mock_tokenizer
