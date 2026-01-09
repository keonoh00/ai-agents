from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse

from ..auth import require_valid_api_key
from ..schemas import ChatMessage, CompletionRequest
from ..utils import simple_text_backend, simple_text_backend_stream

router = APIRouter()


@router.post("/v1/completions", dependencies=[Depends(require_valid_api_key)])
async def completions(req: CompletionRequest):
    now = int(datetime.utcnow().timestamp())
    response_id = f"cmpl-{now}"

    # Normalize prompt to string
    if isinstance(req.prompt, list):
        prompt_str = " ".join(str(p) for p in req.prompt)
    else:
        prompt_str = str(req.prompt)

    if req.stream:
        # Streaming response (Server-Sent Events)
        async def generate_stream():
            # Send initial metadata
            yield f'data: {{"id":"{response_id}","object":"text_completion","created":{now},"model":"{req.model}","choices":[{{"index":0,"text":"","finish_reason":null}}]}}\n\n'
            
            # Stream the response
            async for chunk in simple_text_backend_stream(
                [ChatMessage(role="user", content=prompt_str)],
                model_id=req.model,
                max_tokens=req.max_tokens,
                temperature=req.temperature,
            ):
                if chunk.startswith("data: "):
                    # Parse and reformat for completions endpoint (text instead of delta.content)
                    # Extract content from delta
                    import json
                    try:
                        chunk_data = json.loads(chunk[6:])  # Remove "data: " prefix
                        if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                            delta = chunk_data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield f'data: {{"id":"{response_id}","object":"text_completion","created":{now},"model":"{req.model}","choices":[{{"index":0,"text":"{content}","finish_reason":null}}]}}\n\n'
                    except json.JSONDecodeError:
                        pass
                elif chunk == "data: [DONE]\n\n":
                    # Send final chunk
                    yield f'data: {{"id":"{response_id}","object":"text_completion","created":{now},"model":"{req.model}","choices":[{{"index":0,"text":"","finish_reason":"stop"}}]}}\n\n'
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
    messages = [ChatMessage(role="user", content=prompt_str)]
    answer, prompt_tokens, completion_tokens = simple_text_backend(
        messages, model_id=req.model, max_tokens=req.max_tokens, temperature=req.temperature
    )

    response = {
        "id": response_id,
        "object": "text_completion",
        "created": now,
        "model": req.model,
        "choices": [
            {
                "index": 0,
                "text": answer,
                "finish_reason": "stop",
                "logprobs": None,
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }
    return JSONResponse(response)
