from datetime import datetime
from typing import Dict, Optional, Tuple

from fastapi import APIRouter, Depends
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

from ..auth import require_valid_api_key
from ..models.registry import get_moderation_model_id
from ..schemas import ModerationRequest

router = APIRouter()

# Cache models by model ID to support multiple models
_moderation_models: Dict[str, Tuple[AutoModelForSequenceClassification, AutoTokenizer]] = {}
_moderation_device: Optional[str] = None


def get_moderation_model(model_id: Optional[str] = None) -> Tuple[AutoModelForSequenceClassification, AutoTokenizer]:
    """
    Get or initialize Hugging Face moderation model.
    Supports multiple models via model_id parameter (like OpenAI).
    """
    global _moderation_models, _moderation_device
    
    if _moderation_device is None:
        _moderation_device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Get Hugging Face model ID from OpenAI-style model name
    hf_model_id = get_moderation_model_id(model_id)
    
    # Check cache
    if hf_model_id in _moderation_models:
        return _moderation_models[hf_model_id]
    
    tokenizer = AutoTokenizer.from_pretrained(hf_model_id)
    model = AutoModelForSequenceClassification.from_pretrained(hf_model_id)
    model.to(_moderation_device)
    model.eval()
    
    # Cache the model
    _moderation_models[hf_model_id] = (model, tokenizer)
    
    return model, tokenizer


@router.post("/v1/moderations", dependencies=[Depends(require_valid_api_key)])
def moderations(req: ModerationRequest):
    """
    Real moderation using Hugging Face toxicity detection model.
    Supports model selection via model parameter.
    """
    model, tokenizer = get_moderation_model(req.model)
    
    # Normalize input to list of texts
    if isinstance(req.input, str):
        inputs = [req.input]
    elif isinstance(req.input, list):
        inputs = [str(x) for x in req.input]
    else:
        inputs = [str(req.input)]

    results = []
    for text in inputs:
        # Tokenize and classify
        tokens = tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(_moderation_device)
        
        with torch.no_grad():
            outputs = model(**tokens)
            logits = outputs.logits
            probs = torch.sigmoid(logits).cpu().numpy()[0]
        
        # Map model outputs to OpenAI-style categories
        # The toxic-bert model outputs: toxic, severe_toxic, obscene, threat, insult, identity_hate
        # We'll map these to OpenAI categories
        toxic_score = float(probs[0])  # toxic
        severe_toxic_score = float(probs[1])  # severe_toxic
        obscene_score = float(probs[2])  # obscene (can indicate sexual content)
        threat_score = float(probs[3])  # threat
        insult_score = float(probs[4])  # insult
        identity_hate_score = float(probs[5])  # identity_hate
        
        # Map to OpenAI categories
        hate_score = max(toxic_score, identity_hate_score, insult_score)
        violence_score = threat_score
        # Use obscene as a proxy for sexual content (not perfect but better than 0.0)
        sexual_score = obscene_score * 0.8  # Scale down as obscene != sexual
        # Self-harm detection is harder - use threat as a weak proxy for now
        # In production, you'd want a dedicated self-harm detection model
        self_harm_score = threat_score * 0.3  # Very weak proxy
        
        flagged = any([
            hate_score > 0.5,
            violence_score > 0.5,
            sexual_score > 0.5,
            self_harm_score > 0.5,
        ])
        
        results.append(
            {
                "flagged": flagged,
                "categories": {
                    "hate": hate_score > 0.5,
                    "hate/threatening": hate_score > 0.7,
                    "self-harm": self_harm_score > 0.5,
                    "sexual": sexual_score > 0.5,
                    "sexual/minors": sexual_score > 0.5,
                    "violence": violence_score > 0.5,
                    "violence/graphic": violence_score > 0.7,
                },
                "category_scores": {
                    "hate": hate_score,
                    "hate/threatening": min(hate_score * 1.2, 1.0),
                    "self-harm": self_harm_score,
                    "sexual": sexual_score,
                    "sexual/minors": sexual_score,
                    "violence": violence_score,
                    "violence/graphic": min(violence_score * 1.2, 1.0),
                },
            }
        )

    return {
        "id": f"modr-{int(datetime.utcnow().timestamp())}",
        "model": req.model or "local-moderation",
        "results": results,
    }

