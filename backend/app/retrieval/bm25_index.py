"""
Phase 6, Step 1: BM25 keyword/sparse index over code chunks.

Responsibility: build and query a BM25 index directly from Chunk rows.
Unlike vector embedding, BM25 needs no token-window splitting -- it's
pure term-frequency statistics, so we index each whole function as
one document.
"""

import re
from dataclasses import dataclass, field

from rank_bm25 import BM25Okapi

from app.storage.models import Chunk

# Code-aware tokenization: preserves dotted identifiers (e.g. Session.request)
# while also indexing constituent components, and removes conversational English
# stopwords that have artificially high IDF in codebases.
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_.]+")

STOPWORDS = {
    "what", "when", "where", "which", "who", "whom", "whose", "why", "how",
    "is", "are", "was", "were", "be", "been", "being", "do", "does", "did",
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "for", "of",
    "at", "by", "from", "with", "about", "against", "between", "into", "through",
    "during", "before", "after", "above", "below", "to", "in", "on", "off",
    "walk", "through", "full", "flow", "happens", "called",
}


def tokenize(text: str) -> list[str]:
    tokens = []
    for raw in TOKEN_PATTERN.findall(text):
        t = raw.strip(".").lower()
        if not t or t in STOPWORDS:
            continue
        tokens.append(t)
        if "." in t:
            for part in t.split("."):
                if part and part not in STOPWORDS:
                    tokens.append(part)
        elif "_" in t:
            for part in t.split("_"):
                if part and part not in STOPWORDS:
                    tokens.append(part)
    return tokens


@dataclass
class BM25Index:
    """Holds the fitted BM25 model plus the chunk_id each document maps to."""
    bm25: BM25Okapi
    chunk_ids: list[int]
    file_paths: list[str] = field(default_factory=list)


def build_bm25_index(chunks: list[Chunk]) -> BM25Index:
    """
    Build a BM25 index from Chunk rows.

    Each document combines function_name, class_name, docstring, and
    source_code -- with strong weighting on the chunk's identity (qualified
    name, class, function) so direct name references score highest.
    """
    documents = []
    chunk_ids = []
    file_paths = []

    for chunk in chunks:
        qualified_name = f"{chunk.class_name}.{chunk.function_name}" if chunk.class_name else chunk.function_name
        identity = f"{chunk.function_name} {chunk.class_name or ''} {qualified_name} " * 5
        parts = [
            identity,
            chunk.docstring or "",
            chunk.source_code,
        ]
        combined_text = " ".join(parts)
        documents.append(tokenize(combined_text))
        chunk_ids.append(chunk.id)
        file_paths.append(chunk.file.relative_path if chunk.file else "")

    bm25 = BM25Okapi(documents)
    return BM25Index(bm25=bm25, chunk_ids=chunk_ids, file_paths=file_paths)


def search_bm25(index: BM25Index, query: str, top_k: int = 5) -> list[tuple[int, float]]:
    """
    Search the BM25 index.

    Returns:
        List of (chunk_id, score) tuples, ordered by descending score.
    """
    tokenized_query = tokenize(query)
    scores = index.bm25.get_scores(tokenized_query)

    is_test_query = "test" in query.lower()
    scored_chunks = []
    fps = getattr(index, "file_paths", [""] * len(scores))
    for cid, fp, score in zip(index.chunk_ids, fps, scores):
        if not is_test_query and ("test" in fp.lower()):
            score *= 0.5
        scored_chunks.append((cid, score))

    scored_chunks.sort(key=lambda x: x[1], reverse=True)

    return scored_chunks[:top_k]