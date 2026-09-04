"""
Phase 6 + 9: Hybrid retrieval with RRF fusion and optional metadata filtering.

Responsibility: run dense (vector) and sparse (BM25) retrieval on the
same query, optionally restrict both to results matching a set of
metadata filters, then combine their rankings using Reciprocal Rank
Fusion.
"""

from dataclasses import dataclass

from app.storage.models import Chunk
from app.retrieval.basic_retrieval import RetrievedChunk, retrieve as vector_retrieve
from app.retrieval.bm25_index import BM25Index, search_bm25
from app.retrieval.filters import RetrievalFilters, matches

RRF_K = 60  # standard damping constant used in the original RRF paper


@dataclass
class HybridResult:
    chunk_id: int
    fused_score: float
    function_name: str
    class_name: str | None
    file_path: str
    start_line: int
    end_line: int
    text: str
    is_dependency: bool = False   # NEW: True if pulled in via call-graph expansion, not direct retrieval


def _dedupe_vector_results_by_chunk(vector_results: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """
    Vector search operates at the WINDOW level, so one chunk can appear
    multiple times (e.g. window 1/8 and window 2/8 of the same long
    function). For fusion, we want one rank per CHUNK, so we keep only
    each chunk's best (first-seen / closest) window.
    """
    seen = set()
    deduped = []
    for r in vector_results:
        if r.chunk_id not in seen:
            seen.add(r.chunk_id)
            deduped.append(r)
    return deduped


def reciprocal_rank_fusion(
    vector_results: list[RetrievedChunk],
    bm25_results: list[tuple[int, float]],
) -> dict[int, float]:
    """
    Combine two ranked lists into fused scores, keyed by chunk_id.

    Returns:
        Dict mapping chunk_id -> fused RRF score (higher is better).
    """
    scores: dict[int, float] = {}

    deduped_vector = _dedupe_vector_results_by_chunk(vector_results)
    for rank, result in enumerate(deduped_vector):
        scores[result.chunk_id] = scores.get(result.chunk_id, 0.0) + 1.0 / (RRF_K + rank + 1)

    for rank, (chunk_id, _score) in enumerate(bm25_results):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (RRF_K + rank + 1)

    return scores


def hybrid_retrieve(
    collection,
    bm25_index: BM25Index,
    chunks_by_id: dict[int, Chunk],
    question: str,
    top_k: int = 5,
    candidate_pool_size: int = 20,
    filters: RetrievalFilters | None = None,
) -> list[HybridResult]:
    """
    Run vector + BM25 retrieval, optionally filter by metadata, fuse
    with RRF, and return the top_k fully-hydrated results.

    Args:
        collection: Chroma collection.
        bm25_index: BM25Index built from the same repo's chunks.
        chunks_by_id: dict of chunk_id -> Chunk, used to hydrate metadata
                      for BM25-only results and to check filter criteria.
        question: the user's query.
        top_k: how many final fused results to return.
        candidate_pool_size: how many results to pull from EACH method
                              before fusing (wider net than the final top_k).
        filters: optional RetrievalFilters to restrict results by
                 language, file path prefix, class, or repo_id.
    """
    if filters is None:
        filters = RetrievalFilters()

    vector_results = vector_retrieve(collection, question, top_k=candidate_pool_size)
    bm25_results = search_bm25(bm25_index, question, top_k=candidate_pool_size)

    # Apply filters BEFORE fusion, so filtered-out candidates never
    # influence the ranking at all -- not just hidden from final output.
    # chunks_by_id is used as the single source of truth for metadata
    # (repo_id, language) that isn't carried directly on RetrievedChunk.
    if not filters.is_empty():
        def _chunk_matches(chunk_id: int) -> bool:
            chunk = chunks_by_id.get(chunk_id)
            if chunk is None:
                return False
            return matches(
                filters,
                repo_id=chunk.file.repo_id,
                language=chunk.language,
                file_path=chunk.file.relative_path,
                class_name=chunk.class_name,
            )

        vector_results = [r for r in vector_results if _chunk_matches(r.chunk_id)]
        bm25_results = [(cid, score) for cid, score in bm25_results if _chunk_matches(cid)]

    fused_scores = reciprocal_rank_fusion(vector_results, bm25_results)

    # Build a lookup for vector results' text/metadata (already hydrated).
    vector_by_chunk = {r.chunk_id: r for r in vector_results}

    ranked_chunk_ids = sorted(fused_scores.keys(), key=lambda cid: fused_scores[cid], reverse=True)

    results = []
    for chunk_id in ranked_chunk_ids[:top_k]:
        if chunk_id in vector_by_chunk:
            v = vector_by_chunk[chunk_id]
            results.append(HybridResult(
                chunk_id=chunk_id, fused_score=fused_scores[chunk_id],
                function_name=v.function_name, class_name=v.class_name,
                file_path=v.file_path, start_line=v.start_line, end_line=v.end_line,
                text=v.text,
            ))
        else:
            # BM25-only hit: hydrate from the MySQL Chunk record instead.
            chunk = chunks_by_id.get(chunk_id)
            if chunk is None:
                continue
            results.append(HybridResult(
                chunk_id=chunk_id, fused_score=fused_scores[chunk_id],
                function_name=chunk.function_name, class_name=chunk.class_name,
                file_path=chunk.file.relative_path, start_line=chunk.start_line,
                end_line=chunk.end_line, text=chunk.source_code,
            ))

    return results