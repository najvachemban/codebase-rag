"""
Phase 1, Step 3: Respecting a repository's own .gitignore rules.

Responsibility: load a repo's .gitignore (if present) and provide a way
to check whether a given file path should be excluded according to it.

This is a SECOND filtering layer on top of file_walker.py's hardcoded
EXCLUDED_DIRS / SOURCE_EXTENSIONS -- not a replacement for it.
"""

from pathlib import Path

import pathspec


def load_gitignore_spec(repo_path: Path) -> pathspec.PathSpec | None:
    """
    Load and parse a repository's .gitignore file, if it exists.

    Args:
        repo_path: root directory of the cloned repository.

    Returns:
        A compiled PathSpec object, or None if no .gitignore exists.
    """
    gitignore_path = repo_path / ".gitignore"

    if not gitignore_path.exists():
        return None

    with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    return pathspec.PathSpec.from_lines("gitwildmatch", lines)


def is_ignored(path: Path, repo_path: Path, spec: pathspec.PathSpec | None) -> bool:
    """
    Check whether a file path matches the repo's .gitignore rules.

    Args:
        path: absolute path to the file being checked.
        repo_path: root directory of the cloned repository (for relative matching).
        spec: compiled PathSpec from load_gitignore_spec(), or None.

    Returns:
        True if the file should be excluded per .gitignore rules.
    """
    if spec is None:
        return False

    relative_path = path.relative_to(repo_path)
    return spec.match_file(str(relative_path))