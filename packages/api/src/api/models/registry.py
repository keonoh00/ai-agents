"""
Model registry for mapping OpenAI-style model IDs to Hugging Face model IDs.
Supports multiple models per endpoint type, just like OpenAI.
"""

import os
from typing import Dict, Optional

# Model mappings: OpenAI-style ID -> Hugging Face model ID
LLM_MODELS: Dict[str, str] = {
    "local-llm": os.getenv("LLM_MODEL_ID", "microsoft/DialoGPT-medium"),
    "gpt-3.5-turbo": "microsoft/DialoGPT-medium",  # Alias
    "gpt-4": "microsoft/DialoGPT-large",  # If available
    "dialo-gpt-medium": "microsoft/DialoGPT-medium",
    "dialo-gpt-large": "microsoft/DialoGPT-large",
}

IMAGE_MODELS: Dict[str, str] = {
    "local-image": os.getenv("IMAGE_MODEL_ID", "runwayml/stable-diffusion-v1-5"),
    "dall-e-2": "runwayml/stable-diffusion-v1-5",  # Alias
    "dall-e-3": "stabilityai/stable-diffusion-2-1",  # Better quality
    "stable-diffusion-v1-5": "runwayml/stable-diffusion-v1-5",
    "stable-diffusion-v2-1": "stabilityai/stable-diffusion-2-1",
}

# Edge TTS voice mappings (OpenAI-style model ID -> edge-tts voice name)
# Popular voices: en-US-AriaNeural (female), en-US-GuyNeural (male),
# en-GB-SoniaNeural (British female), etc.
TTS_VOICES: Dict[str, str] = {
    "local-tts": os.getenv("TTS_VOICE", "en-US-AriaNeural"),
    "tts-1": "en-US-AriaNeural",  # Default female voice
    "tts-1-hd": "en-US-AriaNeural",  # Same as tts-1 for edge-tts
    "alloy": "en-US-AriaNeural",  # OpenAI voice name mapping
    "echo": "en-US-GuyNeural",  # Male voice
    "fable": "en-GB-SoniaNeural",  # British female
    "onyx": "en-US-GuyNeural",  # Male voice
    "nova": "en-US-AriaNeural",  # Female voice
    "shimmer": "en-US-AriaNeural",  # Female voice
}

# Common voice names that can be used directly
COMMON_VOICES: Dict[str, str] = {
    "default": "en-US-AriaNeural",
    "aria": "en-US-AriaNeural",
    "guy": "en-US-GuyNeural",
    "sonia": "en-GB-SoniaNeural",
    "jane": "en-US-JennyNeural",
    "davis": "en-US-DavisNeural",
}

EMBEDDING_MODELS: Dict[str, str] = {
    "local-embedding": os.getenv(
        "EMBEDDING_MODEL_ID", "sentence-transformers/all-MiniLM-L6-v2"
    ),
    "text-embedding-ada-002": "sentence-transformers/all-MiniLM-L6-v2",  # Alias
    "text-embedding-3-small": "sentence-transformers/all-MiniLM-L6-v2",
    "text-embedding-3-large": "sentence-transformers/all-mpnet-base-v2",  # Larger model
    "all-minilm-l6-v2": "sentence-transformers/all-MiniLM-L6-v2",
    "all-mpnet-base-v2": "sentence-transformers/all-mpnet-base-v2",
}

MODERATION_MODELS: Dict[str, str] = {
    "local-moderation": os.getenv("MODERATION_MODEL_ID", "unitary/toxic-bert"),
    "text-moderation-stable": "unitary/toxic-bert",
    "text-moderation-latest": "unitary/unbiased-toxic-roberta",  # Alternative
    "toxic-bert": "unitary/toxic-bert",
}


def get_llm_model_id(requested_model: str) -> str:
    """Get Hugging Face model ID from OpenAI-style model name."""
    return LLM_MODELS.get(requested_model, LLM_MODELS["local-llm"])


def get_image_model_id(requested_model: str) -> str:
    """Get Hugging Face model ID from OpenAI-style model name."""
    return IMAGE_MODELS.get(requested_model, IMAGE_MODELS["local-image"])


def get_tts_voice(
    requested_model: Optional[str] = None, requested_voice: Optional[str] = None
) -> str:
    """
    Get edge-tts voice name from OpenAI-style model name or voice name.
    Priority: requested_voice > requested_model > default
    """
    # If voice is explicitly provided, use it (might be a direct voice name or alias)
    if requested_voice:
        # Check if it's a common voice alias
        if requested_voice.lower() in COMMON_VOICES:
            return COMMON_VOICES[requested_voice.lower()]
        # Check if it's already a valid edge-tts voice name (contains "Neural")
        if "Neural" in requested_voice:
            return requested_voice
        # Otherwise, try to find it in TTS_VOICES
        if requested_voice in TTS_VOICES:
            return TTS_VOICES[requested_voice]

    # If model is provided, use it to get voice
    if requested_model:
        return TTS_VOICES.get(requested_model, TTS_VOICES["local-tts"])

    # Default voice
    return TTS_VOICES["local-tts"]


def get_embedding_model_id(requested_model: str) -> str:
    """Get Hugging Face model ID from OpenAI-style model name."""
    return EMBEDDING_MODELS.get(requested_model, EMBEDDING_MODELS["local-embedding"])


def get_moderation_model_id(requested_model: Optional[str]) -> str:
    """Get Hugging Face model ID from OpenAI-style model name."""
    if not requested_model:
        return MODERATION_MODELS["local-moderation"]
    return MODERATION_MODELS.get(requested_model, MODERATION_MODELS["local-moderation"])
