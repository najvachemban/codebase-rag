"""
Phase 5, Step 1: Basic vector-only retrieval.

Responsibility: take a natural-language question, embed it with the
SAME model used for chunks, search Chroma, and return clean,
citation-ready results.
"""

from dataclasses import dataclass

from app.embeddings.embedder import embed_text
from app.storage.vector_store import search


@dataclass
class RetrievedChunk:
    """One search result, shaped for direct use in a prompt or citation."""
    chunk_id: int
    text: str
    function_name: str
    class_name: str | None
    file_path: str
    start_line: int
    end_line: int
    distance: float


def retrieve(collection, question: str, top_k: int = 5) -> list[RetrievedChunk]:
    """
    Embed a question and retrieve the top_k most similar code chunks.

    Args:
        collection: Chroma collection (from vector_store.get_collection).
        question: the user's natural-language question.
        top_k: how many results to return.

    Returns:
        List of RetrievedChunk, ordered by relevance (closest first).
    """
    query_vector = embed_text(question)
    is_test_query = "test" in question.lower()
    pool_size = max(top_k * 6, 30)
    raw_results = search(collection, query_vector=query_vector, top_k=pool_size)

    retrieved = []
    ids = raw_results["ids"][0]
    documents = raw_results["documents"][0]
    metadatas = raw_results["metadatas"][0]
    distances = raw_results["distances"][0]

    for i in range(len(ids)):
        meta = metadatas[i]
        file_path = meta["file_path"]
        dist = distances[i]
        if not is_test_query and ("test" in file_path.lower() or meta["function_name"].startswith("test_")):
            dist += 0.15

        retrieved.append(
            (
                dist,
                RetrievedChunk(
                    chunk_id=meta["chunk_id"],
                    text=documents[i],
                    function_name=meta["function_name"],
                    class_name=meta["class_name"] or None,
                    file_path=file_path,
                    start_line=meta["start_line"],
                    end_line=meta["end_line"],
                    distance=distances[i],
                ),
            )
        )

    retrieved.sort(key=lambda x: x[0])
    return [r for _, r in retrieved[:top_k]]