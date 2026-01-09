import asyncio
import os
import shutil
import subprocess
import tempfile
from typing import Dict, List, Optional

import edge_tts

from .registry import get_tts_voice

# Cache available voices
_available_voices: Optional[List[Dict]] = None

_FFMPEG_CMD_CACHE: Optional[str] = None
_SUPPORTED_FORMATS = {"wav", "mp3", "opus", "flac"}


async def _get_available_voices() -> List[Dict]:
    """Get list of available voices from edge-tts."""
    global _available_voices
    if _available_voices is None:
        voices = await edge_tts.list_voices()
        _available_voices = list(voices) if voices else []
    return _available_voices or []


def get_available_voices() -> List[Dict]:
    """Synchronous wrapper to get available voices."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(_get_available_voices())


def text_to_speech_audio_bytes(
    text: str,
    model_id: Optional[str] = None,
    voice: Optional[str] = None,
    format: str = "wav",
) -> bytes:
    """
    Convert text to speech using edge-tts and return as audio bytes in specified format.
    Supports voice selection and multiple formats (wav, mp3, opus, etc.).

    Args:
        text: Text to convert to speech
        model_id: Model ID (kept for API compatibility, but edge-tts doesn't use models)
        voice: Voice name (e.g., "en-US-AriaNeural", "en-GB-SoniaNeural")
        format: Output format (wav, mp3, opus, flac)

    Returns:
        Audio bytes in the requested format
    """
    # Get voice from registry or use default
    selected_voice = get_tts_voice(model_id, voice)
    target_format = (format or "wav").lower()
    if target_format not in _SUPPORTED_FORMATS:
        target_format = "wav"

    # Generate speech using edge-tts
    async def _generate_speech():
        communicate = edge_tts.Communicate(text, selected_voice)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data

    # Run async function
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    audio_data = loop.run_until_complete(_generate_speech())

    # edge-tts returns MP3 audio by default.
    if target_format == "mp3":
        return audio_data

    return _convert_audio_with_ffmpeg(audio_data, target_format)


def _get_ffmpeg_path() -> str:
    """Resolve ffmpeg binary path once."""
    global _FFMPEG_CMD_CACHE
    if _FFMPEG_CMD_CACHE:
        return _FFMPEG_CMD_CACHE

    candidate = os.environ.get("FFMPEG_PATH", "ffmpeg")
    resolved = shutil.which(candidate)
    if not resolved:
        raise RuntimeError(
            "ffmpeg is required to convert audio formats. "
            "Install ffmpeg and/or set the FFMPEG_PATH environment variable."
        )
    _FFMPEG_CMD_CACHE = resolved
    return resolved


def _convert_audio_with_ffmpeg(audio_bytes: bytes, target_format: str) -> bytes:
    """Convert MP3 bytes to the requested format using ffmpeg."""
    ffmpeg_path = _get_ffmpeg_path()

    src_path = ""
    dst_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as src_file:
            src_file.write(audio_bytes)
            src_file.flush()
            src_path = src_file.name

        with tempfile.NamedTemporaryFile(suffix=f".{target_format}", delete=False) as dst_file:
            dst_path = dst_file.name

        cmd = [ffmpeg_path, "-y", "-loglevel", "error", "-i", src_path]
        if target_format == "wav":
            cmd += ["-c:a", "pcm_s16le"]
        elif target_format == "opus":
            cmd += ["-c:a", "libopus"]
        elif target_format == "flac":
            cmd += ["-c:a", "flac"]
        else:
            cmd += ["-c:a", "copy"]
        cmd.append(dst_path)

        subprocess.run(cmd, check=True)

        with open(dst_path, "rb") as output_file:
            return output_file.read()
    finally:
        if src_path and os.path.exists(src_path):
            os.remove(src_path)
        if dst_path and os.path.exists(dst_path):
            os.remove(dst_path)
