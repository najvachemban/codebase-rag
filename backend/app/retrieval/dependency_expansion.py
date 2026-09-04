"""
Phase 10, Step 2: Expand retrieval results with their direct callees.

Responsibility: for each retrieved chunk, find the functions it calls
(via call_graph.py) and pull in any of those callees that exist as
chunks IN THE SAME FILE -- directly fixing the demonstrated gap where
a matched orchestrator's callees silently drop out of top-K results.

Scoped to same-file matching only, to avoid the risk (identified in
the Step 1 mini task) of attaching an unrelated same-named function
from elsewhere in a large codebase.
"""

from app.storage.models import Chunk
from app.parsing.call_graph import extract_called_functions
from app.retrieval.hybrid_retrieval import HybridResult


def build_function_index(chunks_by_id: dict[int, Chunk]) -> dict[tuple[str, str], int]:
    """
    Build a lookup: (file_path, function_name) -> chunk_id.

    Scoping by file_path (not just function_name alone) is the direct
    mitigation for the false-dependency risk identified earlier --
    two different classes can both have a `send` method, and we only
    want to match the one in the SAME FILE as the caller.
    """
    index = {}
    for chunk_id, chunk in chunks_by_id.items():
        key = (chunk.file.relative_path, chunk.function_name)
        index[key] = chunk_id
    return index


def expand_with_dependencies(
    results: list[HybridResult],
    chunks_by_id: dict[int, Chunk],
    function_index: dict[tuple[str, str], int],
    max_extra_per_result: int = 3,
) -> list[HybridResult]:
    """
    Given a list of retrieved results, find each one's callees (same file
    only) and append any not already present in the result set.

    Args:
        results: the already-retrieved (and possibly reranked) results.
        chunks_by_id: full chunk lookup, for hydrating newly-added dependencies.
        function_index: from build_function_index().
        max_extra_per_result: cap on how many dependencies to pull per result,
                               to avoid unbounded context growth for a function
                               that calls many things.

    Returns:
        The original results, followed by any newly-added dependency chunks
        (marked with is_dependency=True), with duplicates avoided.
    """
    existing_chunk_ids = {r.chunk_id for r in results}
    expanded = list(results)

    for result in results:
        called_names = extract_called_functions(result.text)

        added_for_this_result = 0
        for name in called_names:
            if added_for_this_result >= max_extra_per_result:
                break

            key = (result.file_path, name)
            callee_chunk_id = function_index.get(key)

            if callee_chunk_id is None or callee_chunk_id in existing_chunk_ids:
                continue  # not found in this file, or already in results

            callee_chunk = chunks_by_id[callee_chunk_id]
            expanded.append(HybridResult(
                chunk_id=callee_chunk_id,
                fused_score=0.0,  # not independently ranked -- pulled in structurally
                function_name=callee_chunk.function_name,
                class_name=callee_chunk.class_name,
                file_path=callee_chunk.file.relative_path,
                start_line=callee_chunk.start_line,
                end_line=callee_chunk.end_line,
                text=callee_chunk.source_code,
                is_dependency=True,
            ))
            existing_chunk_ids.add(callee_chunk_id)
            added_for_this_result += 1

    return expanded