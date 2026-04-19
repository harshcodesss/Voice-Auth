"""
Application settings loaded from .env file.
All paths are resolved relative to the backend/ root directory.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Resolve project paths
BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent  # backend/
load_dotenv(BACKEND_ROOT / ".env")


class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # Paths (relative to backend/)
    speaker_db_path: str = "models/speaker_db.pkl"
    upload_dir: str = "uploads"
    data_dir: str = "data/processed"

    # ML
    similarity_threshold: float = 0.75
    chunk_duration_sec: int = 10

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000"

    # Database
    database_url: str = "sqlite:///./voice_auth.db"

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def abs_speaker_db_path(self) -> Path:
        return BACKEND_ROOT / self.speaker_db_path

    @property
    def abs_upload_dir(self) -> Path:
        return BACKEND_ROOT / self.upload_dir

    @property
    def abs_data_dir(self) -> Path:
        return BACKEND_ROOT / self.data_dir

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()

# Ensure critical directories exist on import
settings.abs_upload_dir.mkdir(parents=True, exist_ok=True)
settings.abs_speaker_db_path.parent.mkdir(parents=True, exist_ok=True)
