import pytest
import uvicorn
from fastapi import FastAPI

from .routes import audio, chat, completions, embeddings, images, models, moderations
from .utils import get_llm_model

app = FastAPI(title="OpenAI-style FastAPI Backend with PyTorch Dummy Models")


@app.on_event("startup")
def _load_models() -> None:
    """
    Preload the default text model so the first request doesn't block on download.
    """
    get_llm_model()

# Register all routes
app.include_router(models.router)
app.include_router(chat.router)
app.include_router(completions.router)
app.include_router(embeddings.router)
app.include_router(images.router)
app.include_router(audio.router)
app.include_router(moderations.router)


@app.get("/")
def root():
    return {"status": "ok", "server": "openai-style-fastapi-pytorch"}


@app.get("/health")
def health():
    return {"status": "healthy"}


def main():
    uvicorn.run("api.main:app", host="0.0.0.0", port=8080)


def run_tests():
    """Entry point for 'test' script."""
    import sys

    # Remove the script name from argv, keep the rest for pytest
    exit_code = pytest.main(sys.argv[1:] if len(sys.argv) > 1 else ["-v"])
    sys.exit(exit_code)


def run_server():
    """Entry point for 'serve' script."""
    uvicorn.run("api.main:app", host="0.0.0.0", port=8080)


def run_dev():
    """Entry point for 'dev' script."""
    uvicorn.run("api.main:app", host="0.0.0.0", port=8080, reload=True)
