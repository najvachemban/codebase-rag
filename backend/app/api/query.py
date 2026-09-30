"""
Phase 15 Step 5: POST /query -- ask a question about an indexed repository.

Runs synchronously, unlike indexing: retrieval + one LLM call take
seconds, not minutes, so there's no need to make the client poll.

Known, deliberate limitation (named, not hidden): RetrievalContext --
the BM25 index, function-call index, and exact-name index -- is built
fresh on EVERY request by re-querying all of the repository's chunks
from the database. build_retrieval_context()'s own docstring says it's
meant to be built once per repo/session, not per question; since each
HTTP request here is independent, that reuse doesn't happen yet. A real
production version would cache RetrievalContext per repo_id (in-memory
or Redis, invalidated on re-index). Left for Phase 17.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.repositories import get_db
from app.api.schemas import QueryRequest, QueryResponse, Citation
from app.storage.repository_store import get_repository
from app.storage.chunk_store import get_chunks_for_repository
from app.storage.vector_store import get_client, get_collection
from app.retrieval.rag_pipeline import build_retrieval_context, answer_question
from app.retrieval.filters import RetrievalFilters
from app.retrieval.evidence_check import NO_EVIDENCE_MESSAGE

logger = logging.getLogger(__name__)

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
def query_endpoint(payload: QueryRequest, session: Session = Depends(get_db)) -> QueryResponse:
    """
    Ask a question about an indexed repository.

    Requires status == "completed" -- returns 409 otherwise, naming the
    actual status, so a client can tell "not indexed yet" / "indexing in
    progress" / "indexing failed" apart from a genuine "nothing relevant
    found" answer (which the pipeline reports itself, via abstention,
    not as an error).
    """
    repo = get_repository(session, payload.repository_id)
    if repo is None:
        raise HTTPException(status_code=404, detail=f"Repository {payload.repository_id} not found")

    if repo.status != "completed":
        raise HTTPException(
            status_code=409,
            detail=(
                f"Repository {payload.repository_id} is not ready for querying "
                f"(status: {repo.status}). Wait for indexing to complete."
            ),
        )

    if payload.use_query_rewriting:
        raise HTTPException(
            status_code=501,
            detail="Query rewriting is not yet wired into this endpoint.",
        )

    chunks = get_chunks_for_repository(session, payload.repository_id)

    client = get_client()
    collection = get_collection(client)
    ctx = build_retrieval_context(collection, chunks)

    filters = RetrievalFilters(
        repo_id=payload.repository_id,
        language=payload.language,
        file_path_prefix=payload.path_prefix,
        class_name=payload.class_name,
    )

    result = answer_question(
        ctx,
        payload.question,
        top_k=payload.top_k,
        candidate_pool_size=max(payload.top_k * 4, 20),
        filters=filters,
    )

    abstained = result["answer"] == NO_EVIDENCE_MESSAGE

    citation_check = result["citation_check"]
    citation_warning = None
    if citation_check.get("is_suspicious"):
        unverified = citation_check.get("unverified", [])
        citation_warning = (
            f"Answer references file(s) not found in retrieved context: {', '.join(unverified)}"
        )

    citations = [
        Citation(
            file_path=s["file_path"],
            function_name=s["function_name"],
            class_name=s["class_name"],
            lines=s["lines"],
            is_dependency=s["is_dependency"],
        )
        for s in result["sources"]
    ]

    logger.info(
        "Query answered repository_id=%s abstained=%s sources=%d",
        payload.repository_id, abstained, len(citations),
    )

    return QueryResponse(
        answer=result["answer"],
        citations=citations,
        abstained=abstained,
        citation_warning=citation_warning,
    )