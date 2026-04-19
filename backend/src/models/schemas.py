"""
Pydantic request / response schemas for the speaker recognition API.
"""

from datetime import datetime
from pydantic import BaseModel, Field


# ── Register Speaker ────────────────────────────────

class RegisterSpeakerResponse(BaseModel):
    speaker_name: str
    files_processed: int
    message: str


# ── Chunk‑level prediction ──────────────────────────

class ChunkPrediction(BaseModel):
    chunk_index: int
    start_sec: float
    end_sec: float
    speaker: str
    similarity: float = Field(..., ge=-1.0, le=1.0)
    is_known: bool


# ── Full analysis response ──────────────────────────

class AnalyzeResponse(BaseModel):
    filename: str
    duration_sec: float
    final_speaker: str
    similarity: float
    is_known: bool
    num_chunks: int
    threshold_used: float
    chunks: list[ChunkPrediction]


# ── Speaker list ────────────────────────────────────

class SpeakerInfo(BaseModel):
    name: str
    registered_at: datetime | None = None


class SpeakerListResponse(BaseModel):
    count: int
    speakers: list[SpeakerInfo]


# ── Health ──────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    speakers_loaded: int = 0
    model_ready: bool = False


# ── Generic error ───────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
