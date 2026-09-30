"""
Phase 2, Step 5: Persisting extracted CodeChunks to the database.
Phase 15: added get_chunks_for_repository, needed to build a
RetrievalContext (rag_pipeline.py) for a given repo at query time.
"""

from app.storage.models import Chunk, File
from app.parsing.ast_chunker import CodeChunk


def save_chunks(session, file_id: int, code_chunks: list[CodeChunk]) -> list[Chunk]:
    chunk_rows: list[Chunk] = []
    for c in code_chunks:
        row = Chunk(
            file_id=file_id,
            function_name=c.function_name,
            class_name=c.class_name,
            docstring=c.docstring,
            source_code=c.source_code,
            start_line=c.start_line,
            end_line=c.end_line,
            language=c.language,
        )
        row.imports = c.imports
        chunk_rows.append(row)

    session.add_all(chunk_rows)
    session.commit()
    return chunk_rows


def get_chunks_for_repository(session, repo_id: int) -> list[Chunk]:
    """
    Fetch every Chunk belonging to a repository, joined through File.

    Used by POST /query to build a RetrievalContext (BM25 index,
    function-call index, exact-name index) for that repo.
    """
    return (
        session.query(Chunk)
        .join(File, Chunk.file_id == File.id)
        .filter(File.repo_id == repo_id)
        .all()
    )