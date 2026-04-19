"""
Speaker embedding service — wraps the ML pipeline for use by the API.

Responsibilities:
  - Load / manage the SpeechBrain ECAPA encoder (singleton)
  - Extract embeddings from audio files
  - Load / save the speaker database (joblib)
  - Cosine similarity computation
  - Speaker prediction with Unknown detection
"""

import logging
from pathlib import Path
from collections import defaultdict

import numpy as np
import joblib
import torch
from speechbrain.inference import EncoderClassifier

from src.config.settings import settings

logger = logging.getLogger(__name__)

# ── Singleton model loader ──────────────────────────

_classifier: EncoderClassifier | None = None


def _get_classifier() -> EncoderClassifier:
    """Lazy-load the SpeechBrain ECAPA encoder (first call downloads ~80 MB)."""
    global _classifier
    if _classifier is None:
        logger.info("⏳ Loading SpeechBrain ECAPA model — this may take a moment on first run …")
        _classifier = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir=str(settings.abs_upload_dir.parent / "src" / "ml" / "tmp_model"),
        )
        logger.info("✅ SpeechBrain ECAPA model loaded successfully")
    return _classifier


# ── Speaker database (in-memory + pickle) ──────────
# speaker_db.pkl is the PRIMARY source of truth.
# SQLite only stores optional metadata and can be removed without breaking anything.

_speaker_db: dict[str, np.ndarray] | None = None


def _load_db() -> dict[str, np.ndarray]:
    """Load speaker_db.pkl into memory. Returns empty dict if file is missing."""
    global _speaker_db
    db_path = settings.abs_speaker_db_path
    if _speaker_db is None:
        if db_path.exists():
            _speaker_db = joblib.load(db_path)
            logger.info(f"✅ Speaker DB loaded from {db_path} — {len(_speaker_db)} speaker(s): {list(_speaker_db.keys())}")
        else:
            _speaker_db = {}
            logger.warning(f"⚠️  No speaker_db.pkl found at {db_path} — starting with empty DB")
    return _speaker_db


def _save_db():
    """Persist the in-memory speaker DB to disk."""
    db = _load_db()
    joblib.dump(db, settings.abs_speaker_db_path)
    logger.info(f"💾 Speaker DB saved — {len(db)} speaker(s)")


def reload_db():
    """Force-reload the speaker DB from disk (useful after external changes)."""
    global _speaker_db
    _speaker_db = None
    return _load_db()


# ── Core ML operations ─────────────────────────────

def get_embedding(audio_path: str | Path) -> np.ndarray:
    """Extract a 192-dim ECAPA embedding from an audio file."""
    classifier = _get_classifier()
    signal = classifier.load_audio(str(audio_path))
    embedding = classifier.encode_batch(signal)
    return embedding.squeeze().detach().numpy()


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two embedding vectors."""
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


# ── High-level API methods ─────────────────────────

def register_speaker(name: str, audio_paths: list[str | Path]) -> int:
    """
    Register (or update) a speaker by averaging embeddings from multiple audio files.
    Returns the number of files successfully processed.
    """
    db = _load_db()
    embeddings = []

    for path in audio_paths:
        try:
            emb = get_embedding(path)
            embeddings.append(emb)
            logger.debug(f"  ✓ Extracted embedding from {Path(path).name}")
        except Exception as e:
            logger.warning(f"  ✗ Skipping {path}: {e}")

    if not embeddings:
        raise ValueError("No valid embeddings could be extracted from the uploaded files")

    avg_embedding = np.mean(embeddings, axis=0)

    # If speaker already exists, update with a weighted average
    if name in db:
        existing = db[name]
        db[name] = np.mean([existing, avg_embedding], axis=0)
        logger.info(f"🔄 Updated speaker '{name}' with {len(embeddings)} new file(s)")
    else:
        db[name] = avg_embedding
        logger.info(f"🆕 Registered new speaker '{name}' with {len(embeddings)} file(s)")

    _save_db()
    return len(embeddings)


def predict_speaker(
    audio_path: str | Path,
    threshold: float | None = None,
) -> tuple[str, float, bool]:
    """
    Predict the speaker for a single audio file / chunk.
    Returns: (speaker_name, similarity_score, is_known)

    If best similarity < threshold → returns ("Unknown", score, False).
    No forced classification — if it's not confident, it's Unknown.
    """
    threshold = threshold if threshold is not None else settings.similarity_threshold
    db = _load_db()

    if not db:
        logger.warning("Prediction called with empty speaker DB")
        return "Unknown", 0.0, False

    emb = get_embedding(audio_path)

    best_speaker = "Unknown"
    best_score = -1.0

    for speaker, ref_emb in db.items():
        score = cosine_similarity(emb, ref_emb)
        if score > best_score:
            best_score = score
            best_speaker = speaker

    is_known = best_score >= threshold

    logger.debug(
        f"  Chunk {Path(audio_path).name}: "
        f"best_match={best_speaker} sim={best_score:.4f} "
        f"threshold={threshold} → {'KNOWN' if is_known else 'UNKNOWN'}"
    )

    if not is_known:
        best_speaker = "Unknown"

    return best_speaker, round(best_score, 4), is_known


def aggregate_predictions(
    predictions: list[tuple[str, float, bool]],
    threshold: float | None = None,
) -> tuple[str, float, bool]:
    """
    Aggregate chunk-level predictions into a final result.

    Logic:
    1. Filter chunks — keep ONLY those where is_known=True (similarity >= threshold)
    2. If no chunk passes threshold → return "Unknown"
    3. Group passing chunks by speaker name
    4. Pick the speaker with the highest AVERAGE similarity
    5. Return that as final prediction

    This avoids the old problem where 1 known + 1 unknown → wrong output.
    Weak/uncertain chunks are completely ignored.
    """
    threshold = threshold if threshold is not None else settings.similarity_threshold

    # Step 1: Filter — only keep chunks that passed the threshold
    strong_preds = [(name, score) for name, score, known in predictions if known]

    logger.info(
        f"📊 Aggregation: {len(predictions)} total chunks, "
        f"{len(strong_preds)} above threshold ({threshold}), "
        f"{len(predictions) - len(strong_preds)} discarded"
    )

    # Step 2: If no chunk is confident → Unknown
    if not strong_preds:
        # Report the best score from all chunks for debugging
        all_scores = [s for _, s, _ in predictions]
        best_weak = max(all_scores) if all_scores else 0.0
        logger.info(f"  → Final: Unknown (best weak score was {best_weak:.4f})")
        return "Unknown", round(best_weak, 4), False

    # Step 3: Group by speaker and compute average similarity
    speaker_scores: dict[str, list[float]] = defaultdict(list)
    for name, score in strong_preds:
        speaker_scores[name].append(score)

    # Step 4: Pick speaker with highest average similarity
    best_speaker = None
    best_avg = -1.0

    for speaker, scores in speaker_scores.items():
        avg = float(np.mean(scores))
        logger.debug(f"  Speaker '{speaker}': {len(scores)} chunk(s), avg_sim={avg:.4f}")
        if avg > best_avg:
            best_avg = avg
            best_speaker = speaker

    logger.info(f"  → Final: {best_speaker} (avg similarity: {best_avg:.4f})")
    return best_speaker, round(best_avg, 4), True


def list_speakers() -> list[str]:
    """Return names of all registered speakers from the pickle DB (source of truth)."""
    db = _load_db()
    return sorted(db.keys())


def get_speaker_count() -> int:
    """Return the number of registered speakers."""
    db = _load_db()
    return len(db)


def is_model_ready() -> bool:
    """Check if the SpeechBrain model is loaded."""
    return _classifier is not None
