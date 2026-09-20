"""
Pydantic schemas for the Codebase RAG API.

These define the request/response contract for every endpoint. Keeping them
in one file means the "shape" of the API is visible at a glance, separate
from the endpoint logic itself.

Naming convention used throughout:
    <Thing>Create   -> what the client sends to create something
    <Thing>Response -> what the API sends back
    <Thing>Status    -> an enum of allowed states (kept explicit rather than
                         a bare string, so invalid states are impossible)
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


# ---------------------------------------------------------------------------
# Shared enums
# ---------------------------------------------------------------------------

class IndexingStatus(str, Enum):
    """
    Tracks the lifecycle of a repository's indexing job.

    This is our substitute for a task-queue's built-in job status, since we
    made the deliberate trade-off of using FastAPI BackgroundTasks (no
    external broker/worker) instead of Celery/RQ for this project's scale.
    See Phase 15 architecture notes for the full reasoning.
    """
    PENDING = "pending"       # repository row created, indexing not yet started
    INDEXING = "indexing"     # background job actively running
    COMPLETED = "completed"   # indexing finished successfully
    FAILED = "failed"         # indexing raised an exception; see error_message


# ---------------------------------------------------------------------------
# POST /repositories
# ---------------------------------------------------------------------------

class RepositoryCreate(BaseModel):
    """What the client sends to register a new repository."""
    github_url: HttpUrl = Field(
        ...,
        description="Public GitHub repository URL to clone and index later.",
        examples=["https://github.com/psf/requests"],
    )


class RepositoryResponse(BaseModel):
    """
    What the API returns for a single repository.

    Used by POST /repositories, GET /repositories/{id}, and as the list-item
    shape inside GET /repositories.
    """
    id: int
    github_url: str
    name: str
    status: IndexingStatus
    error_message: Optional[str] = None
    file_count: Optional[int] = Field(
        default=None,
        description="Number of files indexed. Null until indexing completes.",
    )
    chunk_count: Optional[int] = Field(
        default=None,
        description="Number of code chunks embedded. Null until indexing completes.",
    )
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # allows constructing directly from a SQLAlchemy row


# ---------------------------------------------------------------------------
# GET /repositories
# ---------------------------------------------------------------------------

class RepositoryListResponse(BaseModel):
    """Wraps a list so we can add pagination fields later without breaking clients."""
    repositories: list[RepositoryResponse]
    total: int


# ---------------------------------------------------------------------------
# POST /repositories/{id}/index
# ---------------------------------------------------------------------------

class IndexTriggerResponse(BaseModel):
    """
    Returned immediately when an indexing job is accepted.

    Deliberately thin: it does NOT wait for indexing to finish (that's the
    whole point of running it in the background). The client is expected to
    poll GET /repositories/{id} and read `status`.
    """
    repository_id: int
    status: IndexingStatus
    message: str


# ---------------------------------------------------------------------------
# POST /query
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    """What the client sends to ask a question about an indexed repository."""
    repository_id: int
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of candidates to retrieve before fusion/reranking.",
    )
    use_query_rewriting: bool = Field(
        default=False,
        description=(
            "Opt-in only. Phase 8 testing found no clear improvement from "
            "query rewriting on this corpus, so it defaults off."
        ),
    )
    language: Optional[str] = Field(
        default=None, description="Optional metadata filter, e.g. 'python'."
    )
    path_prefix: Optional[str] = Field(
        default=None, description="Optional metadata filter on file path prefix."
    )
    class_name: Optional[str] = Field(
        default=None, description="Optional metadata filter on containing class."
    )


class Citation(BaseModel):
    """One grounding reference backing the answer."""
    file_path: str
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    is_dependency: bool = Field(
        default=False,
        description="True if this chunk was pulled in via Phase 10 dependency expansion.",
    )


class QueryResponse(BaseModel):
    """What the API returns for a question."""
    answer: str
    citations: list[Citation]
    abstained: bool = Field(
        default=False,
        description="True if Phase 13's pre-generation evidence check skipped the LLM entirely.",
    )
    citation_warning: Optional[str] = Field(
        default=None,
        description=(
            "Set if Phase 13's post-generation citation check found a file "
            "referenced in the answer that wasn't actually in retrieved context."
        ),
    )


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    version: str