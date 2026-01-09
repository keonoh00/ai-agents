from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from ..auth import require_valid_api_key
from ..models.image_model import generate_image_base64
from ..schemas import ImageGenerationRequest

router = APIRouter()


@router.post("/v1/images/generations", dependencies=[Depends(require_valid_api_key)])
def image_generations(req: ImageGenerationRequest):
    # Parse size (e.g., "512x512", "1024x1024")
    width, height = 512, 512
    if req.size:
        try:
            parts = req.size.split("x")
            if len(parts) == 2:
                width = int(parts[0])
                height = int(parts[1])
        except (ValueError, AttributeError):
            pass  # Use defaults
    
    # Generate image using real Stable Diffusion model
    # Support model selection like OpenAI (dall-e-2, dall-e-3, etc.)
    b64, estimated_tokens = generate_image_base64(
        prompt=req.prompt,
        model_id=req.model,
        width=width,
        height=height,
        num_inference_steps=20,  # Balance between quality and speed
    )
    
    now = int(datetime.utcnow().timestamp())

    response = {
        "created": now,
        "data": [
            {
                "b64_json": b64,
            }
        ],
        # Note: OpenAI doesn't return usage for images, but we include it for consistency
        "usage": {
            "prompt_tokens": estimated_tokens,
            "total_tokens": estimated_tokens,
        },
    }
    return JSONResponse(response)

