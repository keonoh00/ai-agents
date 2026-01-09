from fastapi import APIRouter, Depends
from fastapi.responses import Response

from ..auth import require_valid_api_key
from ..models.tts_model import text_to_speech_audio_bytes
from ..schemas import AudioSpeechRequest

router = APIRouter()

# Map format to MIME type
FORMAT_MIME_TYPES = {
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "opus": "audio/opus",
    "flac": "audio/flac",
}


@router.post("/v1/audio/speech", dependencies=[Depends(require_valid_api_key)])
def audio_speech(req: AudioSpeechRequest):
    """
    Generate speech using real TTS model.
    Supports model selection, voice selection, and multiple audio formats.
    """
    # Generate speech using real TTS model
    # Support model selection like OpenAI (tts-1, tts-1-hd, etc.)
    # Support voice selection and format conversion
    audio_format = (req.format or "wav").lower()
    audio_bytes = text_to_speech_audio_bytes(
        text=req.input, model_id=req.model, voice=req.voice, format=audio_format
    )
    
    # Get appropriate MIME type
    media_type = FORMAT_MIME_TYPES.get(audio_format, "audio/wav")
    
    return Response(content=audio_bytes, media_type=media_type)

