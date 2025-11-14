# OpenAI-style FastAPI Backend

A FastAPI backend that provides OpenAI-compatible API endpoints using Hugging Face models.

## Features

- **Chat Completions** (`/v1/chat/completions`) - Text generation with streaming support
- **Completions** (`/v1/completions`) - Simple text completion with streaming support
- **Embeddings** (`/v1/embeddings`) - Text embeddings using sentence transformers
- **Image Generation** (`/v1/images/generations`) - Image generation using Stable Diffusion
- **Audio Speech** (`/v1/audio/speech`) - Text-to-speech with multiple formats (wav, mp3, opus, flac)
- **Moderations** (`/v1/moderations`) - Content moderation using toxic-bert
- **Models** (`/v1/models`) - List and retrieve available models

## Installation

```bash
# Install dependencies
uv sync

# Or install with test dependencies
uv sync --extra test
```

### System requirements

- Python 3.14+
- `ffmpeg` binary available in your PATH (required for converting TTS audio to wav/opus/flac).  
  If `ffmpeg` lives elsewhere, set `FFMPEG_PATH=/full/path/to/ffmpeg`.

## Configuration

Set your API key via environment variable:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or it will default to `"change-me-api-key"` (not recommended for production).

## Running the Server

```bash
# Using UV (recommended)
uv run uvicorn api.main:app --host 0.0.0.0 --port 8000

# Using Makefile (convenience)
make serve

# Development mode with auto-reload
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
# Or: make dev

# Or using Python directly
python -m api.main
```

## Testing

Run the test suite:

```bash
# Using UV (recommended)
uv run pytest

# Using Makefile (convenience)
make test

# Run with coverage
uv run pytest --cov=api --cov-report=html

# Run specific test file
uv run pytest tests/test_chat.py
```

## API Usage

All endpoints require authentication via Bearer token:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-llm",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Model Selection

The API supports model selection similar to OpenAI's API. You can specify different models for each task:

- **Text Models**: `local-llm`, `gpt-3.5-turbo`, `gpt-4`, `dialo-gpt-medium`
- **Image Models**: `local-image`, `dall-e-2`, `dall-e-3`, `stable-diffusion-v1-5`
- **TTS Models**: `local-tts`, `tts-1`, `tts-1-hd`, `tacotron2`
- **Embedding Models**: `local-embedding`, `text-embedding-ada-002`, `all-minilm-l6-v2`
- **Moderation Models**: `local-moderation`, `text-moderation-latest`, `toxic-bert`

## Streaming

Streaming is supported for chat completions and completions endpoints:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local-llm",
    "messages": [{"role": "user", "content": "Tell me a story"}],
    "stream": true
  }'
```

## Development

The project structure:

```
api/
├── main.py              # FastAPI app initialization
├── config.py            # Configuration
├── auth.py              # Authentication
├── schemas.py           # Pydantic models
├── utils.py             # LLM utilities
├── models/              # Model implementations
│   ├── image_model.py
│   ├── tts_model.py
│   ├── embedding.py
│   └── registry.py
├── routes/              # API routes
│   ├── chat.py
│   ├── completions.py
│   ├── embeddings.py
│   ├── images.py
│   ├── audio.py
│   ├── moderations.py
│   └── models.py
└── tests/               # Test suite
    ├── conftest.py
    ├── test_chat.py
    ├── test_completions.py
    ├── test_embeddings.py
    ├── test_images.py
    ├── test_audio.py
    ├── test_moderations.py
    ├── test_models.py
    └── test_auth.py
```

