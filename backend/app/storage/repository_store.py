"""
Phase 1, Step 6: Persisting ingestion results (repo + file metadata) to the database.

This is the bridge between the pure in-memory ingestion pipeline
(github_ingestion, file_walker, file_metadata) and durable storage.
"""

from app.storage.models import Repository, File
from app.ingestion.file_metadata import FileMetadata


def save_repository(session, url: str, name: str, status: str = "pending") -> Repository:
    """Create and persist a new Repository row."""
    repo = Repository(url=url, name=name, status=status)
    session.add(repo)
    session.commit()
    session.refresh(repo)
    return repo


def save_files(session, repo_id: int, file_metadata_list: list[FileMetadata]) -> list[File]:
    """Persist a batch of FileMetadata records for a given repository."""
    file_rows = [
        File(
            repo_id=repo_id,
            relative_path=meta.relative_path,
            language=meta.language,
            extension=meta.extension,
            size_bytes=meta.size_bytes,
        )
        for meta in file_metadata_list
    ]
    session.add_all(file_rows)
    session.commit()
    return file_rows


def update_repository_status(session, repo_id: int, status: str) -> None:
    """Update a repository's indexing status (pending -> indexing -> ready/failed)."""
    repo = session.get(Repository, repo_id)
    if repo is not None:
        repo.status = status
        session.commit()