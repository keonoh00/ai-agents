import os

# Single API key, OpenAI-style. Set in your environment:
#   export OPENAI_API_KEY="your-key"
MASTER_API_KEY = (
    os.environ.get("OPENAI_API_KEY")
    or os.environ.get("MASTER_API_KEY")
    or "change-me-api-key"
)

TEXT_MODEL_ID = "gpt-oss:latest"
IMAGE_MODEL_ID = "local-image"
TTS_MODEL_ID = "local-tts"
EMBED_MODEL_ID = "local-embedding"

EMBED_DIM = 128  # dimension for dummy embeddings
