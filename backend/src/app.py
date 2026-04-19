"""
Hindi Speaker Recognition API

FastAPI application entry point.
Embedding-based speaker recognition using SpeechBrain ECAPA-TDNN.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.models.database import init_db
from src.routes import speaker_routes, analysis_routes, health_routes

# ── Logging ─────────────────────────────────────────

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ───────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks before the app begins serving requests."""
    logger.info("🚀 Starting Hindi Speaker Recognition API")

    # Initialize SQLite tables
    init_db()
    logger.info("SQLite database initialized ✓")

    # Pre-load the speaker DB into memory
    from src.services import embedding_service
    embedding_service.reload_db()
    speaker_count = embedding_service.get_speaker_count()
    logger.info(f"Speaker DB loaded — {speaker_count} speaker(s) ✓")

    logger.info(f"Similarity threshold: {settings.similarity_threshold}")
    logger.info(f"Chunk duration: {settings.chunk_duration_sec}s")
    logger.info(f"Uploads directory: {settings.abs_upload_dir}")
    logger.info("API ready — waiting for requests")

    yield  # ← app serves requests here

    logger.info("Shutting down …")


# ── App ─────────────────────────────────────────────

app = FastAPI(
    title="Hindi Speaker Recognition API",
    description=(
        "Embedding-based speaker recognition for Hindi audio. "
        "Register speakers, analyze audio, and identify speakers "
        "using SpeechBrain ECAPA-TDNN cosine similarity."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ──────────────────────────────────────────

app.include_router(health_routes.router)
app.include_router(speaker_routes.router, prefix="/api/v1")
app.include_router(analysis_routes.router, prefix="/api/v1")


# ── Root redirect ──────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "Hindi Speaker Recognition API",
        "docs": "/docs",
        "health": "/health",
    }
