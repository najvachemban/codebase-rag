"""
Phase 11: Context construction.

Responsibility: take the final mixed result set (direct retrieval +
reranked + dependency-expanded chunks) and assemble it into a clean,
ordered, token-budgeted context string ready for the LLM prompt.

Ordering: directly-retrieved results first (by relevance score),
followed by their dependencies -- so the LLM sees "the answer" before
"supporting context," matching how a human would want to read it.

Token budget: results are added greedily in that priority order until
the budget is reached; anything that doesn't fit is dropped and
reported explicitly, never silently truncated mid-function.
"""

from dataclasses import dataclass

from app.retrieval.hybrid_retrieval import HybridResult

# Rough heuristic: ~4 characters per token for English/code text.
# This is an APPROXIMATION -- the real LLM provider's tokenizer would
# give an exact count, but a conservative estimate is sufficient for
# budget-management purposes (we're not trying to hit an exact limit,
# just avoid overshooting it significantly).
CHARS_PER_TOKEN_ESTIMATE = 4


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN_ESTIMATE)


@dataclass
class BuiltContext:
    context_text: str
    included: list[HybridResult]
    dropped: list[HybridResult]
    total_estimated_tokens: int


def _format_block(result: HybridResult) -> str:
    label = f"{result.class_name}.{result.function_name}" if result.class_name else result.function_name
    location = f"{result.file_path}:{result.start_line}-{result.end_line}"
    tag = " [included as a dependency]" if result.is_dependency else ""
    return f"# {label} ({location}){tag}\n{result.text}"


def build_context(results: list[HybridResult], max_tokens: int = 6000) -> BuiltContext:
    """
    Assemble a token-budgeted context string from retrieval results.

    Ordering priority: directly-retrieved results first (already sorted
    by relevance from upstream), then dependency-expanded results --
    so if the budget runs out, we lose supporting context before we
    lose the actual best-matching answers.

    Args:
        results: the full result list (direct + dependencies), in the
                 order produced by retrieval/reranking/expansion.
        max_tokens: approximate token budget for the assembled context.

    Returns:
        BuiltContext with the final prompt-ready text, which results
        were included vs dropped, and the total estimated token count.
    """
    direct = [r for r in results if not r.is_dependency]
    dependencies = [r for r in results if r.is_dependency]
    priority_ordered = direct + dependencies

    included: list[HybridResult] = []
    dropped: list[HybridResult] = []
    running_tokens = 0

    for result in priority_ordered:
        block = _format_block(result)
        block_tokens = estimate_tokens(block)

        if running_tokens + block_tokens > max_tokens:
            dropped.append(result)
            continue

        included.append(result)
        running_tokens += block_tokens

    context_text = "\n\n".join(_format_block(r) for r in included)

    return BuiltContext(
        context_text=context_text,
        included=included,
        dropped=dropped,
        total_estimated_tokens=running_tokens,
    )