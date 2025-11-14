from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import require_valid_api_key
from ..models.registry import (
    EMBEDDING_MODELS,
    IMAGE_MODELS,
    LLM_MODELS,
    MODERATION_MODELS,
    TTS_VOICES,
)
from ..schemas import ModelData

router = APIRouter()

# Collect all available models (like OpenAI's /v1/models endpoint)
ALL_MODELS = {
    **{model_id: "text" for model_id in LLM_MODELS.keys()},
    **{model_id: "image" for model_id in IMAGE_MODELS.keys()},
    **{model_id: "tts" for model_id in TTS_VOICES.keys()},
    **{model_id: "embedding" for model_id in EMBEDDING_MODELS.keys()},
    **{model_id: "moderation" for model_id in MODERATION_MODELS.keys()},
}


@router.get("/v1/models", dependencies=[Depends(require_valid_api_key)])
def list_models():
    """
    List all available models, similar to OpenAI's /v1/models endpoint.
    Supports multiple models per category, just like OpenAI.
    """
    models = [ModelData(id=model_id) for model_id in ALL_MODELS.keys()]
    return {
        "object": "list",
        "data": [m.dict() for m in models],
    }


@router.get("/v1/models/{model_id}", dependencies=[Depends(require_valid_api_key)])
def retrieve_model(model_id: str):
    """
    Retrieve information about a specific model.
    Supports all registered models, not just defaults.
    """
    if model_id not in ALL_MODELS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "message": f"Model '{model_id}' does not exist.",
                    "type": "invalid_request_error",
                    "param": "model",
                    "code": "model_not_found",
                }
            },
        )
    return ModelData(id=model_id).dict()
