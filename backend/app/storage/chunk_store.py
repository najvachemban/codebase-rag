"""
Phase 2, Step 5: Persisting extracted CodeChunks to the database.
"""

from app.storage.models import Chunk
from app.parsing.ast_chunker import CodeChunk


def save_chunks(session, file_id: int, code_chunks: list[CodeChunk]) -> list[Chunk]:
    """Persist a batch of CodeChunk records for a given file.

    Args:
        session: SQLAlchemy session.
        file_id: ID of the File row these chunks belong to.
        code_chunks: List of CodeChunk objects produced by the parser.

    Returns:
        List of Chunk ORM objects that were added to the session.
    """
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
        # Encode imports list as JSON via the property setter on Chunk
        row.imports = c.imports
        chunk_rows.append(row)

    session.add_all(chunk_rows)
    session.commit()
    return chunk_rows
