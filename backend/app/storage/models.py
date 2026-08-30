"""
Phase 1, Step 6: SQLAlchemy ORM models for repositories and files.

Two tables, one-to-many:
  - Repository: one row per indexed repo
  - File: one row per file, foreign-keyed to its repository
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, BigInteger, ForeignKey, DateTime
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(512), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False, default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    files = relationship("File", back_populates="repository", cascade="all, delete-orphan")


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    relative_path = Column(String(1024), nullable=False)
    language = Column(String(64), nullable=False, default="unknown")
    extension = Column(String(32), nullable=True)
    size_bytes = Column(BigInteger, nullable=False, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    repository = relationship("Repository", back_populates="files")