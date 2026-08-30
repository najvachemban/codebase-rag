"""
Phase 1, Step 4: Detecting binary files that slipped past extension filtering.

Responsibility: given a file path, determine whether its actual content
is binary (and therefore not a valid source-code candidate), regardless
of what its extension claims.
"""

from pathlib import Path

# How many bytes to sample from the start of the file.
# Binary content (if present) almost always shows up within this window.
SAMPLE_SIZE = 8192


def is_binary_file(path: Path) -> bool:
    """
    Heuristically determine if a file is binary.

    Uses the same core idea git uses internally: if a null byte appears
    in the first chunk of the file, treat it as binary.

    Args:
        path: path to the file to check.

    Returns:
        True if the file appears to be binary, False if it looks like text.
    """
    try:
        with open(path, "rb") as f:
            chunk = f.read(SAMPLE_SIZE)
    except (OSError, IOError):
        # Unreadable file (permissions, broken symlink, etc.) -- treat
        # as unsafe to process rather than crashing the caller.
        return True

    if b"\x00" in chunk:
        return True

    return False