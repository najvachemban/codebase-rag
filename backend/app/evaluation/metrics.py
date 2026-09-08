"""
Phase 14: Retrieval evaluation metrics, implemented from definitions.

All metrics take:
  - retrieved: an ORDERED list of qualified function names (e.g. "Session.request")
  - expected: a SET of qualified function names considered correct answers
"""


def recall_at_k(retrieved: list[str], expected: set[str]) -> float:
    """Of all the relevant items that exist, what fraction did we find?"""
    if not expected:
        return 1.0
    found = set(retrieved) & expected
    return len(found) / len(expected)


def precision_at_k(retrieved: list[str], expected: set[str]) -> float:
    """Of what we retrieved, what fraction was actually relevant?"""
    if not retrieved:
        return 0.0
    found = set(retrieved) & expected
    return len(found) / len(retrieved)


def mrr(retrieved: list[str], expected: set[str]) -> float:
    """
    Mean Reciprocal Rank: 1/rank of the FIRST relevant result found.
    Rewards getting a correct answer near the top, not just present
    somewhere in the list.
    """
    for i, item in enumerate(retrieved):
        if item in expected:
            return 1.0 / (i + 1)
    return 0.0


def hit_rate(retrieved: list[str], expected: set[str]) -> float:
    """Binary: did we find AT LEAST ONE relevant item at all?"""
    return 1.0 if set(retrieved) & expected else 0.0