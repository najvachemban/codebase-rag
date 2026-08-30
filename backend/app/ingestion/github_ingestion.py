

import subprocess
import tempfile
import uuid
from pathlib import Path


class RepoCloneError(Exception):
    """Raised when a repository fails to clone."""
    pass


def clone_repository(repo_url: str, base_dir: str | None = None) -> Path:
    """
    Shallow-clone a public GitHub repository into an isolated temp directory.

    Args:
        repo_url: HTTPS URL of the GitHub repository, e.g.
                   "https://github.com/psf/requests"
        base_dir: Optional base directory to clone into. If not provided,
                  a new temp directory is created. Useful for tests.

    Returns:
        Path to the local directory containing the cloned repo contents.

    Raises:
        RepoCloneError: if git is unavailable or the clone fails
                        (bad URL, private repo, network issue, etc.)
    """
    job_id = uuid.uuid4().hex[:8]

    if base_dir is None:
        base_dir = tempfile.mkdtemp(prefix=f"codebase-rag-{job_id}-")

    dest_path = Path(base_dir)

    try:
        subprocess.run(
            [
                "git", "clone",
                "--depth", "1",          # shallow clone: no history
                "--single-branch",        # only the default branch
                repo_url,
                str(dest_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.CalledProcessError as e:
        raise RepoCloneError(
            f"Failed to clone {repo_url}: {e.stderr.strip()}"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise RepoCloneError(
            f"Cloning {repo_url} timed out after 120s"
        ) from e

    return dest_path