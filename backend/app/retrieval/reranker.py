"""
Phase 7: Cross-encoder reranking.

Responsibility: given a query and a shortlist of candidate chunks
(from hybrid retrieval), re-score each (query, chunk) PAIR directly
with a cross-encoder for more precise relevance ordering than the
bi-encoder distance/RRF score alone provides.
"""

from sentence_transformers import CrossEncoder

from app.retrieval.hybrid_retrieval import HybridResult

RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_reranker = None


def _get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(RERANKER_MODEL)
    return _reranker


def rerank(query: str, candidates: list[HybridResult], top_k: int = 5) -> list[HybridResult]:
    """
    Re-score and re-order candidates using a cross-encoder.

    Args:
        query: the user's original question.
        candidates: results from hybrid_retrieve (a wider pool, e.g. 20-30).
        top_k: how many results to return after reranking.

    Returns:
        candidates re-ordered by cross-encoder relevance score, truncated to top_k.
        Each result's fused_score is REPLACED with the cross-encoder score,
        so callers can see which stage produced the final ranking.
    """
    if not candidates:
        return []

    model = _get_reranker()

    # Cross-encoder needs (query, document_text) PAIRS as input --
    # this is the key difference from bi-encoder embedding, which
    # only ever sees one text at a time.
    pairs = [(query, c.text) for c in candidates]
    scores = model.predict(pairs)

    scored = list(zip(candidates, scores))
    scored.sort(key=lambda x: x[1], reverse=True)

    reranked = []
    for candidate, score in scored[:top_k]:
        candidate.fused_score = float(score)  # overwrite with cross-encoder score
        reranked.append(candidate)

    return reranked