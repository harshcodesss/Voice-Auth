"""
Audio analysis endpoint — upload audio, split into chunks, predict speakers.
"""

import logging

from fastapi import APIRouter, UploadFile, File, Query, HTTPException

from src.models.schemas import AnalyzeResponse, ChunkPrediction, ErrorResponse
from src.services import embedding_service
from src.utils.audio import (
    save_upload,
    validate_audio_file,
    validate_mime_type,
    get_audio_duration,
    split_audio_into_chunks,
    cleanup_chunks,
    cleanup_file,
)
from src.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["analysis"])


@router.post(
    "/",
    response_model=AnalyzeResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Analyze an audio file for speaker recognition",
    description=(
        "Upload an audio file. Long files are automatically split into chunks. "
        "Each chunk is compared against registered speakers using cosine similarity. "
        "Weak chunks (below threshold) are discarded. "
        "The final prediction uses the speaker with highest average similarity among strong chunks."
    ),
)
async def analyze_audio(
    file: UploadFile = File(..., description="Audio file to analyze"),
    threshold: float = Query(
        default=None,
        ge=0.0,
        le=1.0,
        description="Similarity threshold (overrides server default)",
    ),
    chunk_duration: int = Query(
        default=None,
        ge=2,
        le=30,
        description="Chunk duration in seconds (overrides server default)",
    ),
):
    # Resolve effective settings for this request
    effective_threshold = threshold if threshold is not None else settings.similarity_threshold
    effective_chunk_dur = chunk_duration or settings.chunk_duration_sec

    # Validate file extension and MIME type
    if not validate_audio_file(file.filename):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")

    if not validate_mime_type(file.content_type):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported MIME type: {file.content_type}. Expected an audio file.",
        )

    if embedding_service.get_speaker_count() == 0:
        raise HTTPException(
            status_code=400,
            detail="No speakers registered. Register at least one speaker first.",
        )

    # Save upload and convert to WAV (16 kHz, mono)
    try:
        audio_path = await save_upload(file, sub_dir="analyze")
    except ValueError as e:
        # Raised by save_upload for unsupported/corrupted formats
        logger.warning(f"Audio rejected: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to save upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    try:
        # Get duration
        duration = get_audio_duration(audio_path)

        # Split into chunks
        chunks = split_audio_into_chunks(audio_path, chunk_duration_sec=effective_chunk_dur)

        logger.info(
            f"🎙️  Analyzing '{file.filename}' — "
            f"duration={duration:.1f}s, chunks={len(chunks)}, "
            f"threshold={effective_threshold}, chunk_dur={effective_chunk_dur}s"
        )

        # Predict each chunk
        chunk_results = []
        raw_predictions = []

        for i, chunk in enumerate(chunks):
            try:
                speaker, score, is_known = embedding_service.predict_speaker(
                    chunk["path"],
                    threshold=effective_threshold,
                )

                chunk_results.append(ChunkPrediction(
                    chunk_index=i,
                    start_sec=chunk["start_sec"],
                    end_sec=chunk["end_sec"],
                    speaker=speaker,
                    similarity=score,
                    is_known=is_known,
                ))
                raw_predictions.append((speaker, score, is_known))

            except Exception as e:
                logger.warning(f"Chunk {i} prediction failed: {e}")
                chunk_results.append(ChunkPrediction(
                    chunk_index=i,
                    start_sec=chunk["start_sec"],
                    end_sec=chunk["end_sec"],
                    speaker="Unknown",
                    similarity=0.0,
                    is_known=False,
                ))
                raw_predictions.append(("Unknown", 0.0, False))

        # Aggregate — only considers chunks above threshold
        final_speaker, final_similarity, final_known = embedding_service.aggregate_predictions(
            raw_predictions,
            threshold=effective_threshold,
        )

        # Log to SQLite if available (non-critical, backend works without it)
        _try_log_analysis(
            filename=file.filename,
            duration=duration,
            num_chunks=len(chunks),
            final_speaker=final_speaker,
            final_similarity=final_similarity,
            final_known=final_known,
        )

        return AnalyzeResponse(
            filename=file.filename,
            duration_sec=round(duration, 2),
            final_speaker=final_speaker,
            similarity=final_similarity,
            is_known=final_known,
            num_chunks=len(chunks),
            threshold_used=effective_threshold,
            chunks=chunk_results,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        cleanup_chunks(audio_path)
        cleanup_file(audio_path)  # Remove the converted WAV to save disk space


def _try_log_analysis(
    filename: str,
    duration: float,
    num_chunks: int,
    final_speaker: str,
    final_similarity: float,
    final_known: bool,
):
    """Log analysis to SQLite. Fails silently — SQLite is optional metadata only."""
    try:
        from src.models.database import SessionLocal, AnalysisLog
        db = SessionLocal()
        try:
            db.add(AnalysisLog(
                filename=filename,
                duration_sec=duration,
                num_chunks=num_chunks,
                final_speaker=final_speaker,
                final_similarity=final_similarity,
                final_is_known=str(final_known),
            ))
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.debug(f"SQLite log skipped (non-critical): {e}")
