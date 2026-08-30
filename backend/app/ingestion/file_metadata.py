"""
Phase 1, Step 5: Extracting structured metadata for each candidate file.

Responsibility: turn a raw file Path into a small, structured record
describing it (relative path, detected language, size). This is pure
computation -- no database or network access happens here.
"""

from dataclasses import dataclass
from pathlib import Path

# Maps file extensions to a normalized language name.
# Extended here as we add more languages to SOURCE_EXTENSIONS in file_walker.py.
EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rb": "ruby",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".php": "php",
    ".rs": "rust",
    ".md": "markdown",
}


@dataclass
class FileMetadata:
    """Structured metadata for a single candidate file."""
    relative_path: str   # path relative to the repo root, e.g. "src/auth/login.py"
    absolute_path: Path  # full path on local disk (needed for later reading)
    language: str        # normalized language name, or "unknown"
    extension: str       # e.g. ".py"
    size_bytes: int


def extract_file_metadata(file_path: Path, repo_root: Path) -> FileMetadata:
    """
    Build a FileMetadata record for a single file.

    Args:
        file_path: absolute path to the file.
        repo_root: absolute path to the repository root (for relative path calc).

    Returns:
        A populated FileMetadata instance.
    """
    extension = file_path.suffix
    language = EXTENSION_TO_LANGUAGE.get(extension, "unknown")
    size_bytes = file_path.stat().st_size
    relative_path = str(file_path.relative_to(repo_root))

    return FileMetadata(
        relative_path=relative_path,
        absolute_path=file_path,
        language=language,
        extension=extension,
        size_bytes=size_bytes,
    )