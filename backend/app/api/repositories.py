"""
Phase 15 Steps 3 & 4: Repository registration, lookup, and indexing endpoints.

Endpoints:
    POST /repositories             - register a new repo ('pending' row only)
    GET  /repositories             - list all registered repos
    GET  /repositories/{id}        - fetch one repo by id
    POST /repositories/{id}/index  - kick off background indexing (Step 4)
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.storage.database import get_engine, get_session_factory
from app.storage.repository_store import (
    save_repository,
    get_repository,
    list_repositories,
    update_repository_status,
    count_files_and_chunks,
)
from app.ingestion.index_pipeline import run_indexing_pipeline
from app.api.schemas import (
    RepositoryCreate,
    RepositoryResponse,
    RepositoryListResponse,
    IndexTriggerResponse,
    IndexingStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repositories", tags=["repositories"])

_engine = get_engine()
_SessionFactory = get_session_factory(_engine)


def get_db():
    session = _SessionFactory()
    try:
        yield session
    finally:
        session.close()


def _to_response(repo, session: Session) -> RepositoryResponse:
    file_count, chunk_count = count_files_and_chunks(session, repo.id)
    return RepositoryResponse(
        id=repo.id,
        github_url=repo.url,
        name=repo.name,
        status=repo.status,
        error_message=repo.error_message,
        file_count=file_count,
        chunk_count=chunk_count,
        created_at=repo.created_at,
        updated_at=repo.updated_at,
    )


@router.post("", response_model=RepositoryResponse, status_code=201)
def create_repository_endpoint(
    payload: RepositoryCreate, session: Session = Depends(get_db)
) -> RepositoryResponse:
    """Register a new repository. Creates a 'pending' row only -- does not index."""
    name = str(payload.github_url).rstrip("/").split("/")[-1]
    repo = save_repository(session, url=str(payload.github_url), name=name)
    logger.info("Created repository id=%s url=%s", repo.id, repo.url)
    return _to_response(repo, session)


@router.get("", response_model=RepositoryListResponse)
def list_repositories_endpoint(session: Session = Depends(get_db)) -> RepositoryListResponse:
    """List all registered repositories, newest first."""
    repos = list_repositories(session)
    return RepositoryListResponse(
        repositories=[_to_response(r, session) for r in repos], total=len(repos),
    )


@router.get("/{repository_id}", response_model=RepositoryResponse)
def get_repository_endpoint(
    repository_id: int, session: Session = Depends(get_db)
) -> RepositoryResponse:
    """Fetch one repository by id. Returns 404 if it doesn't exist."""
    repo = get_repository(session, repository_id)
    if repo is None:
        raise HTTPException(status_code=404, detail=f"Repository {repository_id} not found")
    return _to_response(repo, session)


@router.post("/{repository_id}/index", response_model=IndexTriggerResponse, status_code=202)
def trigger_indexing_endpoint(
    repository_id: int,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> IndexTriggerResponse:
    """
    Kick off indexing for a repository in the background.

    Returns 202 Accepted immediately -- the client should poll
    GET /repositories/{id} to see status move from "indexing" to
    "completed" or "failed".

    Returns 409 Conflict if indexing is already running for this repo,
    to prevent two concurrent jobs racing on the same rows. Re-indexing
    an already-"completed" repo is currently allowed but will create
    duplicate File/Chunk rows and orphan old Chroma vectors -- see
    index_pipeline.py's module docstring for why this is a named,
    deliberate gap rather than a hidden one.
    """
    repo = get_repository(session, repository_id)
    if repo is None:
        raise HTTPException(status_code=404, detail=f"Repository {repository_id} not found")

    if repo.status == "indexing":
        raise HTTPException(
            status_code=409,
            detail=f"Repository {repository_id} is already being indexed",
        )

    # Set status synchronously, here, BEFORE returning -- not as the first
    # action inside the background job. BackgroundTasks run only after the
    # response is sent, so if the job set "indexing" itself, a client that
    # polls GET /repositories/{id} immediately after this call could still
    # see the old status for a brief window. Setting it here closes that gap.
    update_repository_status(session, repository_id, "indexing")

    background_tasks.add_task(run_indexing_pipeline, repository_id, repo.url)

    logger.info("Indexing triggered for repository_id=%s", repository_id)

    return IndexTriggerResponse(
        repository_id=repository_id,
        status=IndexingStatus.INDEXING,
        message="Indexing started in the background. Poll GET /repositories/{id} for status.",
    )