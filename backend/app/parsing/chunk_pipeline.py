"""
Phase 2, Step 5: Connects file metadata (Phase 1) to AST chunking (Step 4).

Responsibility: given a FileMetadata record, read its content and run it
through the appropriate chunker if the language is supported. Never
crashes the caller -- unsupported languages or parse errors simply
yield an empty chunk list.
"""

from app.ingestion.file_metadata import FileMetadata
from app.parsing.ast_chunker import extract_function_chunks, CodeChunk

# Only languages with a matching node-type mapping in ast_chunker.py
# should be listed here. Adding a new language means both: (1) adding
# it here, AND (2) verifying ast_chunker's node type names against
# that language's actual Tree-sitter grammar.
SUPPORTED_LANGUAGES = {"python"}


def chunk_file(file_metadata: FileMetadata) -> list[CodeChunk]:
    """
    Read and chunk a single file, if its language is supported.

    Args:
        file_metadata: metadata record from Phase 1's ingestion pipeline.

    Returns:
        List of CodeChunk objects (empty if unsupported or unparsable).
    """
    if file_metadata.language not in SUPPORTED_LANGUAGES:
        return []

    try:
        with open(file_metadata.absolute_path, "r", encoding="utf-8", errors="ignore") as f:
            source_code = f.read()
    except (OSError, IOError):
        return []

    try:
        return extract_function_chunks(source_code, language=file_metadata.language)
    except Exception:
        # A malformed/unparsable file should not crash the whole
        # ingestion job -- skip it and move on.
        return []