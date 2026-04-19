"""
Speaker registration & listing endpoints.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from src.models.schemas import (
    RegisterSpeakerResponse,
    SpeakerListResponse,
    SpeakerInfo,
    ErrorResponse,
)
from src.services import embedding_service
from src.utils.audio import save_upload, validate_audio_file, validate_mime_type

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/speakers", tags=["speakers"])


# ── Helper for optional SQLite ──────────────────────

def _get_db_session():
    """Try to get a SQLite session. Returns None if unavailable."""
    try:
        from src.models.database import SessionLocal
        return SessionLocal()
    except Exception:
        return None


def _close_db(db):
    if db is not None:
        try:
            db.close()
        except Exception:
            pass


# ── Endpoints ───────────────────────────────────────

@router.post(
    "/register",
    response_model=RegisterSpeakerResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Register a new speaker",
    description=(
        "Upload multiple audio files for a speaker. "
        "Embeddings are extracted, averaged, and saved to the speaker database."
    ),
)
async def register_speaker(
    speaker_name: str = Form(..., description="Name / ID of the speaker to register"),
    files: list[UploadFile] = File(..., description="One or more audio files (.wav, .mp3, etc.)"),
):
    # Validate inputs
    if not speaker_name.strip():
        raise HTTPException(status_code=400, detail="Speaker name cannot be empty")

    if not files:
        raise HTTPException(status_code=400, detail="At least one audio file is required")

    for f in files:
        if not validate_audio_file(f.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {f.filename}",
            )
        if not validate_mime_type(f.content_type):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported MIME type for {f.filename}: {f.content_type}",
            )

    # Save uploaded files to disk
    saved_paths = []
    for f in files:
        try:
            path = await save_upload(f, sub_dir=f"register/{speaker_name.strip()}")
            saved_paths.append(path)
        except ValueError as e:
            logger.warning(f"Audio rejected during registration: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to save {f.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save {f.filename}")

    # Extract embeddings & register (this is the core — works without SQLite)
    try:
        files_processed = embedding_service.register_speaker(
            name=speaker_name.strip(),
            audio_paths=saved_paths,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Embedding extraction failed")

    # Optionally persist metadata to SQLite (non-critical)
    db = _get_db_session()
    if db:
        try:
            from src.models.database import SpeakerRecord
            existing = db.query(SpeakerRecord).filter_by(name=speaker_name.strip()).first()
            if existing:
                existing.num_files += files_processed
                existing.updated_at = datetime.now(timezone.utc)
            else:
                db.add(SpeakerRecord(
                    name=speaker_name.strip(),
                    num_files=files_processed,
                ))
            db.commit()
        except Exception as e:
            logger.debug(f"SQLite metadata save skipped (non-critical): {e}")
            db.rollback()
        finally:
            _close_db(db)

    return RegisterSpeakerResponse(
        speaker_name=speaker_name.strip(),
        files_processed=files_processed,
        message=f"Speaker '{speaker_name.strip()}' registered with {files_processed} file(s)",
    )


@router.get(
    "/",
    response_model=SpeakerListResponse,
    summary="List all registered speakers",
)
async def list_speakers():
    # speaker_db.pkl is the source of truth
    names = embedding_service.list_speakers()

    # Enrich with SQLite metadata where available
    speakers = []
    db = _get_db_session()
    try:
        for name in names:
            registered_at = None
            if db:
                try:
                    from src.models.database import SpeakerRecord
                    record = db.query(SpeakerRecord).filter_by(name=name).first()
                    if record:
                        registered_at = record.registered_at
                except Exception:
                    pass
            speakers.append(SpeakerInfo(name=name, registered_at=registered_at))
    finally:
        _close_db(db)

    return SpeakerListResponse(count=len(speakers), speakers=speakers)


@router.delete(
    "/{speaker_name}",
    summary="Remove a registered speaker",
    responses={404: {"model": ErrorResponse}},
)
async def delete_speaker(speaker_name: str):
    """Remove a speaker from the embedding DB (and SQLite if available)."""
    from src.services.embedding_service import _load_db, _save_db

    speaker_db = _load_db()

    if speaker_name not in speaker_db:
        raise HTTPException(status_code=404, detail=f"Speaker '{speaker_name}' not found")

    del speaker_db[speaker_name]
    _save_db()
    logger.info(f"🗑️  Removed speaker '{speaker_name}'")

    # Also remove from SQLite (non-critical)
    db = _get_db_session()
    if db:
        try:
            from src.models.database import SpeakerRecord
            record = db.query(SpeakerRecord).filter_by(name=speaker_name).first()
            if record:
                db.delete(record)
                db.commit()
        except Exception:
            pass
        finally:
            _close_db(db)

    return {"message": f"Speaker '{speaker_name}' removed successfully"}
