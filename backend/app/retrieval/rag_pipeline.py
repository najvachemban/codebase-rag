"""
Phases 5-11: The complete, current RAG pipeline.

Question -> hybrid retrieval (vector + BM25 + RRF) -> exact-name
shortcut -> optional filters -> rerank (cross-encoder, with exact
matches PINNED so they survive reranking) -> dependency expansion
(call graph) -> context construction (token budget) -> LLM -> answer.
"""

from dataclasses import dataclass

from app.storage.models import Chunk
from app.retrieval.bm25_index import BM25Index, build_bm25_index
from app.retrieval.hybrid_retrieval import hybrid_retrieve, HybridResult
from app.retrieval.filters import RetrievalFilters
from app.retrieval.reranker import rerank
from app.retrieval.dependency_expansion import build_function_index, expand_with_dependencies
from app.retrieval.exact_match import NameIndex, build_name_index, find_exact_matches
from app.retrieval.context_builder import build_context
from app.generation.prompt_builder import build_prompt
from app.generation.llm_client import generate_answer


@dataclass
class RetrievalContext:
    """
    Bundles everything that's expensive to build but reusable across
    many queries -- built ONCE per repo/session, not per question.
    """
    collection: object
    bm25_index: BM25Index
    chunks_by_id: dict[int, Chunk]
    function_index: dict[tuple[str, str], int]
    name_index: NameIndex


def build_retrieval_context(collection, chunks: list[Chunk]) -> RetrievalContext:
    """Set up everything needed for repeated querying against one repo."""
    chunks_by_id = {c.id: c for c in chunks}
    bm25_index = build_bm25_index(chunks)
    function_index = build_function_index(chunks_by_id)
    name_index = build_name_index(chunks_by_id)
    return RetrievalContext(
        collection=collection,
        bm25_index=bm25_index,
        chunks_by_id=chunks_by_id,
        function_index=function_index,
        name_index=name_index,
    )


def _hydrate_exact_match(chunk_id: int, chunks_by_id: dict[int, Chunk]) -> HybridResult:
    chunk = chunks_by_id[chunk_id]
    return HybridResult(
        chunk_id=chunk_id,
        fused_score=float("inf"),  # signals "certain match", not a guess
        function_name=chunk.function_name,
        class_name=chunk.class_name,
        file_path=chunk.file.relative_path,
        start_line=chunk.start_line,
        end_line=chunk.end_line,
        text=chunk.source_code,
    )


def answer_question(
    ctx: RetrievalContext,
    question: str,
    top_k: int = 5,
    candidate_pool_size: int = 20,
    filters: RetrievalFilters | None = None,
    use_reranking: bool = True,
    use_dependency_expansion: bool = True,
    max_context_tokens: int = 6000,
) -> dict:
    """
    Run the full pipeline for a single question.

    Returns a dict with the answer text, structured sources (marking
    which were dependency-expanded), and how many results were dropped
    for budget reasons -- full transparency into every stage's decisions.
    """
    # Stage 1: hybrid retrieval (vector + BM25 + RRF), optionally filtered
    candidates = hybrid_retrieve(
        ctx.collection, ctx.bm25_index, ctx.chunks_by_id, question,
        top_k=candidate_pool_size, candidate_pool_size=candidate_pool_size,
        filters=filters,
    )

    # Stage 1.5: exact-name shortcut -- guarantee any directly-named
    # function/class is added to the pool, even if vector/BM25 missed it
    # entirely (the demonstrated failure for short, generic-sounding
    # orchestrator functions with heavily shared vocabulary).
    existing_ids = {c.chunk_id for c in candidates}
    exact_match_ids = find_exact_matches(question, ctx.name_index)
    for chunk_id in exact_match_ids:
        if chunk_id not in existing_ids:
            candidates.append(_hydrate_exact_match(chunk_id, ctx.chunks_by_id))
            existing_ids.add(chunk_id)

    # Stage 2: cross-encoder reranking, narrowing to top_k.
    # Exact-name matches are PINNED -- they must survive to the final
    # result regardless of the cross-encoder's score, since the user
    # named them directly. (This was the real bug: Stage 1.5 injected
    # them into the pool, but reranking could still cut them if the
    # model judged their generic-looking text as unconvincing.)
    if use_reranking and candidates:
        reranked = rerank(question, candidates, top_k=top_k)
        reranked_ids = {c.chunk_id for c in reranked}

        missing_exact_matches = [cid for cid in exact_match_ids if cid not in reranked_ids]
        for chunk_id in missing_exact_matches:
            if reranked:
                reranked.pop()  # drop the lowest-ranked result to make room
            reranked.append(_hydrate_exact_match(chunk_id, ctx.chunks_by_id))

        candidates = reranked
    else:
        candidates = candidates[:top_k]

    # Stage 3: pull in direct dependencies (same-file callees)
    if use_dependency_expansion:
        candidates = expand_with_dependencies(candidates, ctx.chunks_by_id, ctx.function_index)

    # Stage 4: assemble a token-budgeted, priority-ordered context
    built_context = build_context(candidates, max_tokens=max_context_tokens)

    # Stage 5: generate the answer
    prompt = build_prompt(question, built_context.included)
    answer = generate_answer(prompt)

    return {
        "question": question,
        "answer": answer,
        "sources": [
            {
                "file_path": r.file_path,
                "function_name": r.function_name,
                "class_name": r.class_name,
                "lines": f"{r.start_line}-{r.end_line}",
                "is_dependency": r.is_dependency,
            }
            for r in built_context.included
        ],
        "dropped_for_budget": len(built_context.dropped),
        "estimated_context_tokens": built_context.total_estimated_tokens,
    }