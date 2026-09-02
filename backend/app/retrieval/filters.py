"""
Phase 9: Repository-aware retrieval filters.

Responsibility: define filter criteria (language, repo, path prefix,
class) and check whether a given result's metadata satisfies them.
"""

from dataclasses import dataclass


@dataclass
class RetrievalFilters:
    repo_id: int | None = None
    language: str | None = None
    file_path_prefix: str | None = None   # e.g. "src/auth/" to scope to a directory
    class_name: str | None = None

    def is_empty(self) -> bool:
        return not any([self.repo_id, self.language, self.file_path_prefix, self.class_name])


def matches(filters: RetrievalFilters, repo_id: int, language: str,
            file_path: str, class_name: str | None) -> bool:
    """Check whether one result's metadata satisfies the given filters."""
    if filters.is_empty():
        return True

    if filters.repo_id is not None and repo_id != filters.repo_id:
        return False
    if filters.language is not None and language != filters.language:
        return False
    if filters.file_path_prefix is not None and not file_path.startswith(filters.file_path_prefix):
        return False
    if filters.class_name is not None and class_name != filters.class_name:
        return False

    return True