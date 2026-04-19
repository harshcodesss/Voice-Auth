"""
Health check endpoint.
"""

from fastapi import APIRouter
from src.models.schemas import HealthResponse
from src.services import embedding_service

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns API status, speaker count, and model readiness.",
)
async def health_check():
    return HealthResponse(
        status="ok",
        speakers_loaded=embedding_service.get_speaker_count(),
        model_ready=embedding_service.is_model_ready(),
    )
