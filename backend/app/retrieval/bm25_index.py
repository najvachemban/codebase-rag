"""
Phase 6, Step 1: BM25 keyword/sparse index over code chunks.

Responsibility: build and query a BM25 index directly from Chunk rows.
Unlike vector embedding, BM25 needs no token-window splitting -- it's
pure term-frequency statistics, so we index each whole function as
one document.
"""

import re
from dataclasses import dataclass

from rank_bm25 import BM25Okapi

from app.storage.models import Chunk

# Simple code-aware tokenizer: splits on non-alphanumeric characters,
# which naturally separates snake_case pieces (by underscore) and
# punctuation, while keeping camelCase as one token for now (a real
# limitation worth naming -- splitting camelCase too is a possible
# future improvement if evaluation shows it matters).
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_PATTERN.findall(text)]


@dataclass
class BM25Index:
    """Holds the fitted BM25 model plus the chunk_id each document maps to."""
    bm25: BM25Okapi
    chunk_ids: list[int]


def build_bm25_index(chunks: list[Chunk]) -> BM25Index:
    """
    Build a BM25 index from Chunk rows.

    Each document combines function_name, class_name, docstring, and
    source_code -- so a search for a name or a described concept can
    both match, even if the exact term only appears in one of these
    fields (e.g. a well-named function with a sparse body).
    """
    documents = []
    chunk_ids = []

    for chunk in chunks:
        parts = [
            chunk.function_name,
            chunk.class_name or "",
            chunk.docstring or "",
            chunk.source_code,
        ]
        combined_text = " ".join(parts)
        documents.append(tokenize(combined_text))
        chunk_ids.append(chunk.id)

    bm25 = BM25Okapi(documents)
    return BM25Index(bm25=bm25, chunk_ids=chunk_ids)


def search_bm25(index: BM25Index, query: str, top_k: int = 5) -> list[tuple[int, float]]:
    """
    Search the BM25 index.

    Returns:
        List of (chunk_id, score) tuples, ordered by descending score.
    """
    tokenized_query = tokenize(query)
    scores = index.bm25.get_scores(tokenized_query)

    scored_chunks = list(zip(index.chunk_ids, scores))
    scored_chunks.sort(key=lambda x: x[1], reverse=True)

    return scored_chunks[:top_k]