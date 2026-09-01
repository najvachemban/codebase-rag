
"""
Phase 6, Step 2: Hybrid retrieval -- fuse vector + BM25 rankings with RRF.

Responsibility: run dense (vector) and sparse (BM25) retrieval on the
same query, then combine their rankings using Reciprocal Rank Fusion,
which only relies on rank position -- not raw scores -- since the two
methods' scores are not on comparable scales.
"""

from dataclasses import dataclass

from app.storage.models import Chunk
from app.retrieval.basic_retrieval import RetrievedChunk, retrieve as vector_retrieve
from app.retrieval.bm25_index import BM25Index, search_bm25

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
) -> list[HybridResult]:
    """
    Run vector + BM25 retrieval, fuse with RRF, and return the top_k
    fully-hydrated results.

    Args:
        collection: Chroma collection.
        bm25_index: BM25Index built from the same repo's chunks.
        chunks_by_id: dict of chunk_id -> Chunk, used to hydrate metadata
                      for results that only came from BM25 (which doesn't
                      carry file path / line info the way vector results do).
        question: the user's query.
        top_k: how many final fused results to return.
        candidate_pool_size: how many results to pull from EACH method
                              before fusing (wider net than the final top_k).
    """
    vector_results = vector_retrieve(collection, question, top_k=candidate_pool_size)
    bm25_results = search_bm25(bm25_index, question, top_k=candidate_pool_size)

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