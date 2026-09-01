"""
Phase 3, Step 2 (updated for Phase 4): Full embedding pipeline.

Now also carries repo_id and file relative_path through, via the
Chunk -> File relationship, so results are citation-ready.
"""

from dataclasses import dataclass

from app.storage.models import Chunk
from app.embeddings.token_splitter import split_into_windows
from app.embeddings.embedder import embed_batch


@dataclass
class EmbeddedWindow:
    chunk_id: int
    window_index: int
    total_windows: int
    text: str
    vector: list[float]
    function_name: str
    class_name: str | None
    start_line: int
    end_line: int
    language: str
    repo_id: int
    file_path: str


def embed_chunks(chunks: list[Chunk]) -> list[EmbeddedWindow]:
    pending = []
    for chunk in chunks:
        windows = split_into_windows(chunk.source_code)
        for window in windows:
            pending.append((chunk, window))

    all_texts = [window.text for _, window in pending]
    all_vectors = embed_batch(all_texts)

    results = []
    for (chunk, window), vector in zip(pending, all_vectors):
        results.append(
            EmbeddedWindow(
                chunk_id=chunk.id,
                window_index=window.window_index,
                total_windows=window.total_windows,
                text=window.text,
                vector=vector,
                function_name=chunk.function_name,
                class_name=chunk.class_name,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                language=chunk.language,
                repo_id=chunk.file.repo_id,        # via Chunk -> File relationship
                file_path=chunk.file.relative_path,
            )
        )
    return results