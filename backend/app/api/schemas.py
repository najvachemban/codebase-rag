from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class IndexingStatus(str, Enum):
    PENDING = "pending"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"


class RepositoryCreate(BaseModel):
    github_url: HttpUrl = Field(...)


class RepositoryResponse(BaseModel):
    id: int
    github_url: str
    name: str
    status: IndexingStatus
    error_message: Optional[str] = None
    file_count: Optional[int] = None
    chunk_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RepositoryListResponse(BaseModel):
    repositories: list[RepositoryResponse]
    total: int


class IndexTriggerResponse(BaseModel):
    repository_id: int
    status: IndexingStatus
    message: str


class QueryRequest(BaseModel):
    repository_id: int
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=50)
    use_query_rewriting: bool = Field(
        default=False,
        description=(
            "Phase 8 finding: no clear improvement from query rewriting on "
            "this corpus. Not yet wired into this endpoint -- requesting "
            "True currently returns 501."
        ),
    )
    language: Optional[str] = None
    path_prefix: Optional[str] = None
    class_name: Optional[str] = None


class Citation(BaseModel):
    """
    One grounding reference backing the answer.

    `lines` matches answer_question()'s real output shape exactly
    (a pre-formatted "start-end" string), rather than inventing a
    start_line/end_line split the pipeline doesn't actually produce.
    """
    file_path: str
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    lines: Optional[str] = None
    is_dependency: bool = False


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    abstained: bool = False
    citation_warning: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str