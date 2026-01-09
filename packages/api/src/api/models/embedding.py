from typing import Dict, List, Optional, Tuple

from sentence_transformers import SentenceTransformer
import torch

from .registry import get_embedding_model_id

# Cache models by model ID to support multiple models
_embedding_models: Dict[str, SentenceTransformer] = {}


def get_embedding_model(model_id: Optional[str] = None) -> SentenceTransformer:
    """
    Get or initialize Hugging Face embedding model.
    Supports multiple models via model_id parameter (like OpenAI).
    """
    global _embedding_models
    
    # Get Hugging Face model ID from OpenAI-style model name
    hf_model_id = get_embedding_model_id(model_id) if model_id else get_embedding_model_id("local-embedding")
    
    # Check cache
    if hf_model_id in _embedding_models:
        return _embedding_models[hf_model_id]
    
    model = SentenceTransformer(hf_model_id, device="cuda" if torch.cuda.is_available() else "cpu")
    
    # Cache the model
    _embedding_models[hf_model_id] = model
    
    return model


def text_to_embedding_vector(
    text: str, model_id: Optional[str] = None, dim: Optional[int] = None
) -> Tuple[List[float], int]:
    """
    Generate real semantic embeddings from text using Hugging Face model.
    Supports model selection via model_id parameter.
    Returns: (embedding_vector, token_count)
    """
    model = get_embedding_model(model_id)
    
    # Generate embedding
    embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    
    # Count tokens (approximate - use model's tokenizer if available)
    # For sentence-transformers, we can use the underlying tokenizer
    if hasattr(model, "tokenizer"):
        token_count = len(model.tokenizer.encode(text))
    else:
        # Fallback: approximate token count (roughly 4 chars per token)
        token_count = len(text) // 4
    
    # If dim is specified and different, we'd need to project, but typically we use the model's native dim
    return embedding.tolist(), token_count
