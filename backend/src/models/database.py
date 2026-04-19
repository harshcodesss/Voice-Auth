"""
SQLite database setup using SQLAlchemy for optional speaker metadata persistence.
"""

from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.orm import sessionmaker, declarative_base

from src.config.settings import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=settings.debug,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class SpeakerRecord(Base):
    """Metadata row for a registered speaker."""
    __tablename__ = "speakers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)
    num_files = Column(Integer, default=0)
    registered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))


class AnalysisLog(Base):
    """Optional log of analysis requests for audit / debugging."""
    __tablename__ = "analysis_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String, nullable=False)
    duration_sec = Column(Float)
    num_chunks = Column(Integer)
    final_speaker = Column(String)
    final_similarity = Column(Float)
    final_is_known = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency that yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
