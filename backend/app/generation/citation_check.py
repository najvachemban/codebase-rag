"""
Phase 13: Post-generation citation verification.

Responsibility: after the LLM generates an answer, check whether any
file paths it mentions actually correspond to files that were present
in the retrieved context. This is a HEURISTIC safety net, not a proof
of correctness -- it catches obvious hallucinated file references, but
text-pattern matching can miss things or produce false positives.
"""

import re

FILE_PATH_PATTERN = re.compile(r"[\w\-/\\]+\.(?:py|js|ts|jsx|tsx|java|go|rb|c|cpp|h|hpp|cs|php|rs)")


def extract_mentioned_file_paths(answer_text: str) -> set[str]:
    """Find anything in the answer that looks like a source file path."""
    return set(FILE_PATH_PATTERN.findall(answer_text))


def verify_citations(answer_text: str, allowed_file_paths: set[str]) -> dict:
    """
    Check whether file paths mentioned in the answer were actually
    present in the retrieved context.

    Args:
        answer_text: the LLM's generated answer.
        allowed_file_paths: the set of file paths that were genuinely
                             included in the context sent to the LLM.

    Returns:
        Dict with 'mentioned', 'unverified' (mentioned but not in
        allowed set -- possible hallucination), and 'is_suspicious'
        (True if any unverified paths were found).
    """
    mentioned = extract_mentioned_file_paths(answer_text)
    # Normalize path separators for comparison (Windows vs Unix)
    normalized_allowed = {p.replace("\\", "/") for p in allowed_file_paths}
    normalized_mentioned = {p.replace("\\", "/") for p in mentioned}

    unverified = normalized_mentioned - normalized_allowed

    return {
        "mentioned": sorted(normalized_mentioned),
        "unverified": sorted(unverified),
        "is_suspicious": len(unverified) > 0,
    }