"""
Phase 8: Query rewriting.

Responsibility: use the LLM to transform a natural-language question
into a more search-optimized query BEFORE retrieval. The original
question is still used later for the actual answer generation --
this only affects what we search FOR, not what we ANSWER.

Per project philosophy: this must be measurably validated before being
treated as a default-on step -- see compare_query_rewriting.py.
"""

from app.generation.llm_client import generate_answer

REWRITE_PROMPT_TEMPLATE = """You are helping optimize a search query for a code search engine.
Given a natural-language question about a codebase, rewrite it into a short,
keyword-dense search query that includes likely function names, class names,
and technical terms a developer might have actually used in the code.

Only output the rewritten query, nothing else -- no explanation, no quotes.

Question: {question}
Rewritten search query:"""


def rewrite_query(question: str) -> str:
    """
    Rewrite a natural-language question into a search-optimized query.

    Args:
        question: the user's original question.

    Returns:
        A rewritten, search-optimized version of the question.
        Falls back to the original question if rewriting fails.
    """
    prompt = REWRITE_PROMPT_TEMPLATE.format(question=question)
    try:
        rewritten = generate_answer(prompt)
        return rewritten.strip()
    except Exception:
        # If the LLM call fails for any reason, retrieval should still
        # work using the original question -- rewriting is an enhancement,
        # not a hard dependency.
        return question