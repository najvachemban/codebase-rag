"""
Phase 13: Pre-generation evidence sufficiency check.

Responsibility: before calling the LLM at all, check whether retrieval
found ANYTHING. If nothing was found, return a deterministic response
instead of calling the LLM -- this guarantees correct abstention for
the "nothing retrieved" case, rather than relying on prompt instructions
alone (which the model could ignore).
"""

NO_EVIDENCE_MESSAGE = (
    "I couldn't find any code in this repository relevant to your question. "
    "This could mean the functionality doesn't exist here, or the question "
    "may need to be phrased differently (e.g. using specific function or "
    "class names if you know them)."
)


def has_sufficient_evidence(candidates: list) -> bool:
    """
    The simplest, most certain check: did retrieval find anything at all?
    More nuanced confidence scoring could be added later (e.g. score
    thresholds), but an EMPTY result set is the one case we can flag
    with total certainty, with no risk of false positives.
    """
    return len(candidates) > 0