"""
sarvam.py — Sarvam AI integration for Hindi translation and TTS audio narration.
Fixed: proper WAV concatenation, logging instead of silent errors.
"""

import io
import os
import wave
import base64
import logging
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
TRANSLATE_URL = "https://api.sarvam.ai/translate"
TTS_URL = "https://api.sarvam.ai/text-to-speech"


def translate_to_hindi(text: str) -> str:
    """
    Translate English text to Hindi using Sarvam Translate API.
    Falls back gracefully if API key is missing or request fails.
    """
    if not SARVAM_API_KEY:
        return f"[Hindi translation unavailable — add SARVAM_API_KEY to .env]\n\n{text}"

    try:
        payload = {
            "input": text,
            "source_language_code": "en-IN",
            "target_language_code": "hi-IN",
            "speaker_gender": "Female",
            "mode": "formal",
            "model": "mayura:v1",
            "enable_preprocessing": True,
        }
        headers = {
            "api-subscription-key": SARVAM_API_KEY,
            "Content-Type": "application/json",
        }
        response = requests.post(TRANSLATE_URL, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json().get("translated_text", text)
    except Exception as e:
        logger.warning(f"Sarvam translation failed: {e}")
        return f"[Translation error: {e}]\n\n{text}"


def translate_training_content(data: dict) -> dict:
    """
    Return a new dict with all user-visible strings translated to Hindi.
    Preserves structure; only translates content fields.
    """
    hindi = dict(data)

    hindi["title"] = translate_to_hindi(data.get("title", ""))
    hindi["objective"] = translate_to_hindi(data.get("objective", ""))

    hindi["summary_points"] = [
        translate_to_hindi(pt) for pt in data.get("summary_points", [])
    ]

    hindi["training_steps"] = []
    for step in data.get("training_steps", []):
        hindi_step = dict(step)
        hindi_step["title"] = translate_to_hindi(step.get("title", ""))
        hindi_step["content"] = translate_to_hindi(step.get("content", ""))
        hindi_step["common_mistakes"] = [
            translate_to_hindi(m) for m in step.get("common_mistakes", [])
        ]
        hindi_step["pro_tips"] = [
            translate_to_hindi(t) for t in step.get("pro_tips", [])
        ]
        hindi["training_steps"].append(hindi_step)

    hindi["quiz"] = []
    for q in data.get("quiz", []):
        hindi_q = dict(q)
        hindi_q["question"] = translate_to_hindi(q.get("question", ""))
        hindi_q["explanation"] = translate_to_hindi(q.get("explanation", ""))
        hindi["quiz"].append(hindi_q)

    hindi["skills_covered"] = [
        translate_to_hindi(s) for s in data.get("skills_covered", [])
    ]

    return hindi


def generate_audio(text: str, language: str = "hi-IN") -> tuple[Optional[bytes], Optional[str]]:
    """
    Generate audio narration using Sarvam TTS (Bulbul).

    Returns:
        (audio_bytes, error_message) — audio_bytes is WAV bytes or None.
        error_message is None on success, descriptive string on failure.
    """
    if not SARVAM_API_KEY:
        return None, "SARVAM_API_KEY not configured"

    # Sarvam TTS has a 500-char limit per request — chunk if needed
    chunks = _chunk_text(text, max_chars=500)
    audio_segments = []
    errors = []

    for i, chunk in enumerate(chunks):
        try:
            payload = {
                "inputs": [chunk],
                "target_language_code": language,
                "speaker": "meera",
                "pitch": 0,
                "pace": 1.0,
                "loudness": 1.5,
                "speech_sample_rate": 22050,
                "enable_preprocessing": True,
                "model": "bulbul:v1",
            }
            headers = {
                "api-subscription-key": SARVAM_API_KEY,
                "Content-Type": "application/json",
            }
            resp = requests.post(TTS_URL, json=payload, headers=headers, timeout=20)
            resp.raise_for_status()
            audio_b64 = resp.json()["audios"][0]
            audio_bytes = base64.b64decode(audio_b64)
            audio_segments.append(audio_bytes)
        except Exception as e:
            error_msg = f"TTS chunk {i + 1}/{len(chunks)} failed: {e}"
            logger.warning(error_msg)
            errors.append(error_msg)

    if not audio_segments:
        return None, "; ".join(errors) if errors else "No audio generated"

    # Properly concatenate WAV segments using the wave module
    merged = _merge_wav_segments(audio_segments)
    error_summary = "; ".join(errors) if errors else None
    return merged, error_summary


def _merge_wav_segments(segments: list[bytes]) -> bytes:
    """
    Properly merge multiple WAV byte segments into a single valid WAV file.
    Uses Python's wave module to handle headers correctly.
    """
    if len(segments) == 1:
        return segments[0]

    # Read params from first segment
    first_wav = io.BytesIO(segments[0])
    try:
        with wave.open(first_wav, "rb") as w:
            params = w.getparams()
            all_frames = [w.readframes(w.getnframes())]
    except wave.Error:
        # If the first segment isn't valid WAV, fall back to simple concat
        logger.warning("First audio segment is not valid WAV, returning as-is")
        return segments[0]

    # Read frames from remaining segments
    for seg_bytes in segments[1:]:
        try:
            seg_buf = io.BytesIO(seg_bytes)
            with wave.open(seg_buf, "rb") as w:
                all_frames.append(w.readframes(w.getnframes()))
        except wave.Error as e:
            logger.warning(f"Skipping invalid WAV segment: {e}")
            continue

    # Write merged WAV
    output = io.BytesIO()
    with wave.open(output, "wb") as out_wav:
        out_wav.setparams(params)
        for frame_data in all_frames:
            out_wav.writeframes(frame_data)

    return output.getvalue()


def _chunk_text(text: str, max_chars: int = 500) -> list[str]:
    """Split text into sentence-aware chunks under max_chars."""
    sentences = text.replace(". ", ".|").split("|")
    chunks = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) <= max_chars:
            current += sentence + " "
        else:
            if current:
                chunks.append(current.strip())
            current = sentence + " "
    if current:
        chunks.append(current.strip())
    return chunks if chunks else [text[:max_chars]]
