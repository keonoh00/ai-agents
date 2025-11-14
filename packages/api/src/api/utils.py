from typing import AsyncGenerator, Dict, Optional, Protocol, Tuple, cast

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedTokenizer,
)

from api.models.registry import get_llm_model_id
from api.schemas import ChatMessage


class GenerativeModel(Protocol):
    """Protocol for models that support text generation."""

    def generate(
        self,
        inputs: torch.Tensor,
        max_new_tokens: int,
        temperature: float,
        do_sample: bool,
        pad_token_id: Optional[int],
        streamer: Optional[object] = None,
    ) -> torch.Tensor:
        """Generate text from inputs."""
        ...

    def to(self, device: str) -> "GenerativeModel":
        """Move model to device."""
        ...

    def eval(self) -> "GenerativeModel":
        """Set model to evaluation mode."""
        ...


# Cache models by model ID to support multiple models
_llm_models: Dict[str, Tuple[GenerativeModel, PreTrainedTokenizer]] = {}
_llm_device: Optional[str] = None


def get_llm_model(
    model_id: Optional[str] = None,
) -> Tuple[GenerativeModel, PreTrainedTokenizer]:
    """
    Get or initialize Hugging Face LLM for text generation.
    Supports multiple models via model_id parameter (like OpenAI).
    """
    global _llm_models, _llm_device

    if _llm_device is None:
        _llm_device = "cuda" if torch.cuda.is_available() else "cpu"

    # Get Hugging Face model ID from OpenAI-style model name
    hf_model_id = (
        get_llm_model_id(model_id) if model_id else get_llm_model_id("local-llm")
    )

    # Check cache
    if hf_model_id in _llm_models:
        return _llm_models[hf_model_id]

    tokenizer = cast(PreTrainedTokenizer, AutoTokenizer.from_pretrained(hf_model_id))
    model = cast(GenerativeModel, AutoModelForCausalLM.from_pretrained(hf_model_id))
    if _llm_device is not None:
        model = model.to(_llm_device)
    model = model.eval()

    # Set pad_token if not exists
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Cache the model
    _llm_models[hf_model_id] = (model, tokenizer)

    return model, tokenizer


def count_tokens(text: str, tokenizer: PreTrainedTokenizer) -> int:
    """Count tokens in text using the tokenizer."""
    return len(tokenizer.encode(text))


def simple_text_backend(
    messages: list[ChatMessage],
    model_id: Optional[str] = None,
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> Tuple[str, int, int]:
    """
    Generate text response using Hugging Face LLM.
    Returns: (response_text, prompt_tokens, completion_tokens)
    """
    model, tokenizer = get_llm_model(model_id)

    # Format messages for the model
    # Extract user messages and system message if present
    user_contents = [m.content for m in messages if m.role == "user"]
    system_content = next((m.content for m in messages if m.role == "system"), None)

    if not user_contents:
        return "No user message provided.", 0, 0

    # Build prompt
    if system_content:
        prompt = f"{system_content}\n\nUser: {user_contents[-1]}"
    else:
        prompt = user_contents[-1]  # Use the last user message

    # Count prompt tokens
    prompt_tokens = count_tokens(prompt, tokenizer)

    # Tokenize and generate
    inputs = cast(torch.Tensor, tokenizer.encode(prompt, return_tensors="pt")).to(
        _llm_device
    )

    with torch.no_grad():
        eos_token_id = tokenizer.eos_token_id
        pad_token_id: Optional[int] = (
            int(eos_token_id)
            if eos_token_id is not None and isinstance(eos_token_id, (int, str))
            else None
        )
        generate_output = model.generate(
            inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True,
            pad_token_id=pad_token_id,
        )
        outputs = cast(torch.Tensor, generate_output)

    # Decode response
    full_response = cast(str, tokenizer.decode(outputs[0], skip_special_tokens=True))

    # Remove the prompt from the response
    if prompt in full_response:
        response = full_response.replace(prompt, "").strip()
    else:
        response = (
            full_response[len(prompt) :].strip()
            if len(full_response) > len(prompt)
            else full_response
        )

    # Count completion tokens
    completion_tokens = count_tokens(response, tokenizer)

    return (
        response if response else "I'm sorry, I couldn't generate a response.",
        prompt_tokens,
        completion_tokens,
    )


async def simple_text_backend_stream(
    messages: list[ChatMessage],
    model_id: Optional[str] = None,
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> AsyncGenerator[str, None]:
    """
    Generate text response with streaming using Hugging Face LLM.
    Yields tokens as they are generated (OpenAI-style streaming).
    """
    model, tokenizer = get_llm_model(model_id)

    # Format messages for the model
    user_contents = [m.content for m in messages if m.role == "user"]
    system_content = next((m.content for m in messages if m.role == "system"), None)

    if not user_contents:
        yield 'data: {"choices":[{"delta":{"content":"No user message provided."}}]}\n\n'
        return

    # Build prompt
    if system_content:
        prompt = f"{system_content}\n\nUser: {user_contents[-1]}"
    else:
        prompt = user_contents[-1]

    # Tokenize
    inputs = cast(torch.Tensor, tokenizer.encode(prompt, return_tensors="pt")).to(
        _llm_device
    )
    input_length = inputs.shape[1]

    # Generate with streaming using TextIteratorStreamer
    from threading import Thread

    from transformers import TextIteratorStreamer

    streamer = TextIteratorStreamer(
        cast(AutoTokenizer, tokenizer), skip_prompt=True, skip_special_tokens=True
    )

    eos_token_id = tokenizer.eos_token_id
    pad_token_id: Optional[int] = (
        int(eos_token_id)
        if eos_token_id is not None and isinstance(eos_token_id, (int, str))
        else None
    )
    generation_kwargs = {
        "inputs": inputs,
        "max_new_tokens": max_tokens,
        "temperature": temperature,
        "do_sample": True,
        "pad_token_id": pad_token_id,
        "streamer": streamer,
    }

    # Run generation in a separate thread
    def run_generation() -> None:
        model.generate(**generation_kwargs)

    thread = Thread(target=run_generation)
    thread.start()

    # Stream tokens as they're generated
    generated_text = ""
    for new_text in streamer:
        if new_text:
            # Escape JSON special characters
            escaped_text = (
                new_text.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\r", "\\r")
            )
            generated_text += new_text
            yield f'data: {{"choices":[{{"delta":{{"content":"{escaped_text}"}}}}]}}\n\n'

    thread.join()

    # Send final done message
    yield "data: [DONE]\n\n"
