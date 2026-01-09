import base64
from io import BytesIO
from typing import Dict, Optional, Tuple

import torch
from diffusers import StableDiffusionPipeline
from PIL import Image

from .registry import get_image_model_id

# Cache pipelines by model ID to support multiple models
_image_pipelines: Dict[str, StableDiffusionPipeline] = {}
_image_device: Optional[str] = None


def get_image_model(model_id: Optional[str] = None) -> StableDiffusionPipeline:
    """
    Get or initialize Stable Diffusion pipeline for image generation.
    Supports multiple models via model_id parameter (like OpenAI).
    """
    global _image_pipelines, _image_device

    if _image_device is None:
        _image_device = "cuda" if torch.cuda.is_available() else "cpu"

    # Get Hugging Face model ID from OpenAI-style model name
    hf_model_id = (
        get_image_model_id(model_id) if model_id else get_image_model_id("local-image")
    )

    # Check cache
    if hf_model_id in _image_pipelines:
        return _image_pipelines[hf_model_id]

    # Use float16 for faster inference if CUDA is available
    dtype = torch.float16 if _image_device == "cuda" else torch.float32

    pipeline = StableDiffusionPipeline.from_pretrained(
        hf_model_id,
        torch_dtype=dtype,
        safety_checker=None,  # Disable safety checker for faster inference
        requires_safety_checker=False,
    )
    pipeline = pipeline.to(_image_device)
    pipeline.set_progress_bar_config(disable=True)

    # Cache the pipeline
    _image_pipelines[hf_model_id] = pipeline

    return pipeline


def generate_image_base64(
    prompt: str,
    model_id: Optional[str] = None,
    width: int = 512,
    height: int = 512,
    num_inference_steps: int = 20,
) -> Tuple[str, int]:
    """
    Generate an image from a prompt and return as base64 PNG string.
    Supports model selection via model_id parameter.
    """
    pipeline = get_image_model(model_id)

    with torch.no_grad():
        image = pipeline(
            prompt=prompt,
            width=width,
            height=height,
            num_inference_steps=num_inference_steps,
            guidance_scale=7.5,
        ).images[0]

    # Convert PIL Image to base64
    buf = BytesIO()
    image.save(buf, format="PNG")
    raw = buf.getvalue()

    # Estimate token count (rough approximation: ~4 chars per token, prompt length)
    # This is a rough estimate since we don't have the actual tokenizer for image generation
    estimated_tokens = len(prompt) // 4

    return base64.b64encode(raw).decode("utf-8"), estimated_tokens
