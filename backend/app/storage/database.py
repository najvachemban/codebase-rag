"""
Phase 1, Step 6: Database engine and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.storage.models import Base


def get_engine(database_url: str | None = None):
    """
    Create a SQLAlchemy engine. Accepts an override URL so tests
    can point at SQLite instead of the real MySQL instance.
    """
    url = database_url or settings.database_url
    return create_engine(url, echo=False)


def get_session_factory(engine):
    return sessionmaker(bind=engine)


def init_db(engine):
    """Create all tables if they don't already exist."""
    Base.metadata.create_all(engine)