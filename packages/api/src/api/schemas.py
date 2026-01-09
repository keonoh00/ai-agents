from typing import Any, List, Literal, Optional

from pydantic import BaseModel


class ModelData(BaseModel):
    id: str
    object: str = "model"
    owned_by: str = "local-owner"


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False  # not implemented


class CompletionRequest(BaseModel):
    model: str
    prompt: Any  # string or list; we'll normalize to a single string
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False  # not implemented


class EmbeddingsRequest(BaseModel):
    model: str
    input: Any  # string or list of strings


class ImageGenerationRequest(BaseModel):
    model: str
    prompt: str
    n: Optional[int] = 1
    size: Optional[str] = "64x64"  # kept for API compatibility


class AudioSpeechRequest(BaseModel):
    model: str
    input: str  # text to speak
    voice: Optional[str] = "default"
    format: Optional[str] = "wav"  # "wav" or others; we'll always return wav


class ModerationRequest(BaseModel):
    model: Optional[str] = None
    input: Any
