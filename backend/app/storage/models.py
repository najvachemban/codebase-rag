"""
Phase 1 & 2: SQLAlchemy ORM models for repositories, files, and code chunks.

Three tables:
  - Repository: one row per indexed repo
  - File: one row per file, foreign-keyed to its repository
  - Chunk: one row per extracted function/method, foreign-keyed to its file
"""

import json
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, BigInteger, ForeignKey, DateTime, Text
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
    chunks = relationship("Chunk", back_populates="file", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    function_name = Column(String(255), nullable=False)
    class_name = Column(String(255), nullable=True)
    docstring = Column(Text, nullable=True)
    source_code = Column(Text, nullable=False)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    language = Column(String(64), nullable=False)
    imports_json = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    file = relationship("File", back_populates="chunks")

    @property
    def imports(self) -> list[str]:
        return json.loads(self.imports_json)

    @imports.setter
    def imports(self, value: list[str]) -> None:
        self.imports_json = json.dumps(value)