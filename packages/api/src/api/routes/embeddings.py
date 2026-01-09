from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from ..auth import require_valid_api_key
from ..models.embedding import text_to_embedding_vector
from ..schemas import EmbeddingsRequest

router = APIRouter()


@router.post("/v1/embeddings", dependencies=[Depends(require_valid_api_key)])
def embeddings(req: EmbeddingsRequest):
    # Normalize input to list of strings
    if isinstance(req.input, str):
        texts = [req.input]
    elif isinstance(req.input, list):
        texts = [str(x) for x in req.input]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "message": "input must be a string or array of strings",
                    "type": "invalid_request_error",
                    "param": "input",
                    "code": None,
                }
            },
        )

    data = []
    total_tokens = 0
    for i, text in enumerate(texts):
        # Support model selection like OpenAI (text-embedding-ada-002, etc.)
        emb, token_count = text_to_embedding_vector(text, model_id=req.model)
        total_tokens += token_count
        data.append(
            {
                "object": "embedding",
                "embedding": emb,
                "index": i,
            }
        )

    response = {
        "object": "list",
        "data": data,
        "model": req.model,
        "usage": {
            "prompt_tokens": total_tokens,
            "total_tokens": total_tokens,
        },
    }
    return JSONResponse(response)

