from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse

from ..auth import require_valid_api_key
from ..schemas import ChatCompletionRequest
from ..utils import simple_text_backend, simple_text_backend_stream

router = APIRouter()


@router.post("/v1/chat/completions", dependencies=[Depends(require_valid_api_key)])
async def chat_completions(req: ChatCompletionRequest):
    now = int(datetime.utcnow().timestamp())
    response_id = f"chatcmpl-{now}"

    if req.stream:
        # Streaming response (Server-Sent Events)
        async def generate_stream():
            # Send initial metadata
            yield f'data: {{"id":"{response_id}","object":"chat.completion.chunk","created":{now},"model":"{req.model}","choices":[{{"index":0,"delta":{{"role":"assistant","content":""}},"finish_reason":null}}]}}\n\n'
            
            # Stream the response
            full_content = ""
            async for chunk in simple_text_backend_stream(
                req.messages,
                model_id=req.model,
                max_tokens=req.max_tokens,
                temperature=req.temperature,
            ):
                if chunk.startswith("data: "):
                    full_content += chunk
                    yield chunk
                elif chunk == "data: [DONE]\n\n":
                    # Send final chunk with finish_reason
                    yield f'data: {{"id":"{response_id}","object":"chat.completion.chunk","created":{now},"model":"{req.model}","choices":[{{"index":0,"delta":{{}},"finish_reason":"stop"}}]}}\n\n'
                    yield chunk

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    # Non-streaming response
    answer, prompt_tokens, completion_tokens = simple_text_backend(
        req.messages, model_id=req.model, max_tokens=req.max_tokens, temperature=req.temperature
    )

    response = {
        "id": response_id,
        "object": "chat.completion",
        "created": now,
        "model": req.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": answer},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }
    return JSONResponse(response)

