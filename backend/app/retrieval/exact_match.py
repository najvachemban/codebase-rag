"""
Phase 10.5 (refinement): Exact-name shortcut.

Responsibility: detect when a question directly names a real function
or class (e.g. "Session.request()", "merge_environment_settings"),
and guarantee that exact chunk is included in the candidate pool --
bypassing the "does this sound relevant" similarity search entirely,
since an exact name match doesn't need to be inferred, it's already known.

Motivated by a demonstrated failure: short, coordinator-style functions
with generic/shared vocabulary can be invisible to both vector search
and BM25, even when the user names them explicitly in their question.
"""

import re
from dataclasses import dataclass

from app.storage.models import Chunk

# Matches: "Session.request", "request()", "merge_environment_settings",
# "self.send" -- basically dotted-or-plain identifier-looking tokens,
# optionally followed by parentheses.
NAME_PATTERN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*(?:\(\))?")


@dataclass
class NameIndex:
    # "function_name" -> list of chunk_ids (a name can exist in multiple classes/files)
    by_function_name: dict[str, list[int]]
    # "ClassName.function_name" -> chunk_id (unambiguous when class is specified)
    by_qualified_name: dict[str, int]


def build_name_index(chunks_by_id: dict[int, Chunk]) -> NameIndex:
    by_function_name: dict[str, list[int]] = {}
    by_qualified_name: dict[str, int] = {}

    for chunk_id, chunk in chunks_by_id.items():
        by_function_name.setdefault(chunk.function_name, []).append(chunk_id)
        if chunk.class_name:
            qualified = f"{chunk.class_name}.{chunk.function_name}"
            by_qualified_name[qualified] = chunk_id

    return NameIndex(by_function_name=by_function_name, by_qualified_name=by_qualified_name)


def extract_candidate_names(question: str) -> list[str]:
    """Pull out tokens from the question that look like identifiers."""
    return [m.group(1) for m in NAME_PATTERN.finditer(question)]


def find_exact_matches(question: str, name_index: NameIndex, max_matches: int = 3) -> list[int]:
    """
    Find chunk_ids for any function/class name mentioned directly in
    the question. Qualified names (Class.method) are checked first,
    since they're unambiguous; bare names fall back to matching any
    chunk with that function name (could match multiple candidates).
    """
    candidates = extract_candidate_names(question)
    matched_chunk_ids: list[int] = []

    for candidate in candidates:
        if len(matched_chunk_ids) >= max_matches:
            break

        if candidate in name_index.by_qualified_name:
            chunk_id = name_index.by_qualified_name[candidate]
            if chunk_id not in matched_chunk_ids:
                matched_chunk_ids.append(chunk_id)
            continue

        if candidate in name_index.by_function_name:
            for chunk_id in name_index.by_function_name[candidate]:
                if chunk_id not in matched_chunk_ids and len(matched_chunk_ids) < max_matches:
                    matched_chunk_ids.append(chunk_id)

    return matched_chunk_ids