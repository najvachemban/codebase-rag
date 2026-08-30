"""
Phase 1, Step 2: Walking the cloned repository's file tree.

Responsibility: given a local directory, return a clean list of candidate
file paths worth further inspection (language detection, chunking, etc.)

This step does NOT read file contents. It only makes decisions based on
directory names and file extensions -- the cheapest possible filter,
applied first.
"""

from pathlib import Path

# Directories we never want to walk into at all.
EXCLUDED_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".pytest_cache", "vendor",
    ".idea", ".vscode", "coverage", "target",
}

# File extensions we consider "source code" candidates for now.
# This will grow as we add language support in later steps.
SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".php", ".rs", ".md",
}


def walk_repository(repo_path: Path) -> list[Path]:
    """
    Walk a cloned repository and return candidate file paths.

    Args:
        repo_path: root directory of the cloned repository.

    Returns:
        List of absolute Paths to files worth further processing.
    """
    candidates: list[Path] = []

    for path in repo_path.rglob("*"):
        # Skip anything inside an excluded directory, at any depth.
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue

        if path.is_file() and path.suffix in SOURCE_EXTENSIONS:
            candidates.append(path)

    return candidates