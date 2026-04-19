"""
File handling utilities — saving uploads, converting formats, validating audio,
splitting into chunks.

Conversion pipeline:
  upload → detect format → convert_to_wav (16 kHz, mono) → librosa.load ✅

This replaces the old flow that assumed everything was already WAV:
  upload → librosa.load ❌
"""

import os
import uuid
import shutil
import logging
import subprocess
from pathlib import Path

import librosa
import soundfile as sf
import numpy as np
from fastapi import UploadFile

from src.config.settings import settings

logger = logging.getLogger(__name__)

# ── Constants ───────────────────────────────────────

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".webm", ".opus"}

ALLOWED_MIME_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/mpeg",
    "audio/mp3",
    "audio/webm",
    "audio/ogg",
    "audio/flac",
    "audio/x-flac",
    "audio/mp4",
    "audio/x-m4a",
    "audio/opus",
    "video/webm",      # browser MediaRecorder sometimes reports video/webm even for audio-only
    "application/octet-stream",  # fallback when browser doesn't set MIME
}

TARGET_SR = 16000       # Target sample rate for all converted audio
TARGET_CHANNELS = 1     # Mono


# ── Validation ──────────────────────────────────────

def validate_audio_file(filename: str) -> bool:
    """Check if the uploaded file has a supported audio extension."""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def validate_mime_type(content_type: str | None) -> bool:
    """
    Check if the MIME type is an accepted audio format.
    Returns True if accepted or if content_type is None/empty (browser may not always send it).
    """
    if not content_type:
        return True  # Be lenient — we'll validate the actual file content during conversion
    return content_type.lower() in ALLOWED_MIME_TYPES


# ── Audio conversion ───────────────────────────────

def _find_ffmpeg() -> str:
    """Locate the ffmpeg binary. Checks common Homebrew paths on macOS."""
    # Check PATH first
    for name in ("ffmpeg",):
        result = shutil.which(name)
        if result:
            return result

    # Common Homebrew paths on macOS
    for path in ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"):
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    raise FileNotFoundError(
        "ffmpeg not found. Install with: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)"
    )


def convert_to_wav(input_path: str | Path) -> Path:
    """
    Convert any audio file to WAV (16 kHz, mono, PCM s16le) using ffmpeg.

    If the input is already a 16 kHz mono WAV, the conversion is still fast
    (ffmpeg transcodes in-memory) and guarantees a clean file for librosa.

    Returns the path to the converted WAV file.
    The caller is responsible for cleanup.
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Output goes next to the input with _converted.wav suffix
    output_path = input_path.with_suffix(".converted.wav")

    ffmpeg_bin = _find_ffmpeg()

    cmd = [
        ffmpeg_bin,
        "-y",                    # Overwrite without asking
        "-i", str(input_path),   # Input file
        "-vn",                   # Drop video stream (webm may have video metadata)
        "-acodec", "pcm_s16le",  # 16-bit PCM encoding
        "-ar", str(TARGET_SR),   # 16 kHz sample rate
        "-ac", str(TARGET_CHANNELS),  # Mono
        str(output_path),
    ]

    logger.info(
        f"🔄 Converting audio: {input_path.name} ({input_path.suffix}) → WAV "
        f"(sr={TARGET_SR}, mono, pcm_s16le)"
    )

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout for very long files
        )

        if result.returncode != 0:
            stderr_tail = result.stderr[-500:] if result.stderr else "no stderr"
            logger.error(f"ffmpeg conversion failed (exit {result.returncode}): {stderr_tail}")
            raise RuntimeError(f"Audio conversion failed: {stderr_tail}")

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError("ffmpeg produced empty or missing output file")

        logger.info(f"✅ Conversion successful: {output_path.name} ({output_path.stat().st_size} bytes)")
        return output_path

    except subprocess.TimeoutExpired:
        logger.error(f"ffmpeg timed out converting {input_path.name}")
        raise RuntimeError("Audio conversion timed out — file may be too large")
    except FileNotFoundError:
        raise  # Re-raise ffmpeg not found
    except RuntimeError:
        raise  # Re-raise our own errors
    except Exception as e:
        logger.error(f"Unexpected error during conversion: {e}")
        raise RuntimeError(f"Audio conversion failed: {e}")


# ── File saving ─────────────────────────────────────

async def save_upload(file: UploadFile, sub_dir: str = "") -> Path:
    """
    Save an uploaded file to disk, then convert it to WAV (16 kHz, mono).

    Returns the path to the converted WAV file.
    The original upload is deleted after successful conversion to save space.
    """
    if not validate_audio_file(file.filename):
        raise ValueError(f"Unsupported file type: {file.filename}")

    if not validate_mime_type(file.content_type):
        raise ValueError(
            f"Unsupported MIME type: {file.content_type}. "
            f"Expected audio file (wav, mp3, webm, etc.)"
        )

    # Save the raw upload with its original extension
    ext = Path(file.filename).suffix or ".webm"  # Default to .webm if no extension
    unique_name = f"{uuid.uuid4().hex}{ext}"

    target_dir = settings.abs_upload_dir / sub_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    raw_path = target_dir / unique_name

    with open(raw_path, "wb") as f:
        content = await file.read()
        f.write(content)

    logger.info(
        f"📥 Saved upload: {file.filename} → {raw_path.name} "
        f"({len(content)} bytes, content_type={file.content_type})"
    )

    # Convert to standard WAV
    try:
        wav_path = convert_to_wav(raw_path)
    except Exception as e:
        # Clean up the raw file on failure
        raw_path.unlink(missing_ok=True)
        raise ValueError(f"Unsupported or corrupted audio format: {e}")

    # Delete original to save space (conversion succeeded)
    try:
        raw_path.unlink(missing_ok=True)
        logger.debug(f"🗑️ Deleted raw upload: {raw_path.name}")
    except Exception:
        pass  # Non-critical

    return wav_path


# ── Audio info & chunking ──────────────────────────

def get_audio_duration(file_path: str | Path) -> float:
    """
    Return audio duration in seconds.
    Expects a converted WAV file (16 kHz mono).
    """
    y, sr = librosa.load(str(file_path), sr=None, mono=True)
    return float(len(y) / sr)


def split_audio_into_chunks(
    file_path: str | Path,
    chunk_duration_sec: int | None = None,
    sr: int = TARGET_SR,
) -> list[dict]:
    """
    Split an audio file into fixed-duration chunks.
    Returns a list of dicts: { 'path': Path, 'start_sec': float, 'end_sec': float }
    If the audio is shorter than chunk_duration, returns the original file as a single chunk.

    Expects a converted WAV file (16 kHz mono) — use save_upload or convert_to_wav first.
    """
    chunk_duration_sec = chunk_duration_sec or settings.chunk_duration_sec
    file_path = Path(file_path)

    y, sr_loaded = librosa.load(str(file_path), sr=sr, mono=True)
    total_duration = len(y) / sr_loaded

    # No splitting needed for short audio
    if total_duration <= chunk_duration_sec * 1.5:
        return [{
            "path": file_path,
            "start_sec": 0.0,
            "end_sec": round(total_duration, 2),
        }]

    chunk_samples = chunk_duration_sec * sr_loaded
    chunks = []

    # Create a temp directory for chunks alongside the source file
    chunks_dir = file_path.parent / f"{file_path.stem}_chunks"
    chunks_dir.mkdir(exist_ok=True)

    for i, start in enumerate(range(0, len(y), chunk_samples)):
        end = min(start + chunk_samples, len(y))
        chunk_audio = y[start:end]

        # Skip very short trailing chunks (< 1 second)
        if len(chunk_audio) < sr_loaded:
            continue

        chunk_path = chunks_dir / f"chunk_{i:03d}.wav"
        sf.write(str(chunk_path), chunk_audio, sr_loaded)

        chunks.append({
            "path": chunk_path,
            "start_sec": round(start / sr_loaded, 2),
            "end_sec": round(end / sr_loaded, 2),
        })

    return chunks


def cleanup_chunks(file_path: str | Path):
    """Remove temporary chunk directory created during analysis."""
    chunks_dir = Path(file_path).parent / f"{Path(file_path).stem}_chunks"
    if chunks_dir.exists():
        shutil.rmtree(chunks_dir)


def cleanup_file(file_path: str | Path):
    """Remove a single file (used to clean up converted WAV after analysis)."""
    path = Path(file_path)
    if path.exists():
        try:
            path.unlink()
            logger.debug(f"🗑️ Cleaned up: {path.name}")
        except Exception:
            pass
