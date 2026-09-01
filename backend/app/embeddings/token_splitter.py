"""
Phase 3, Step 1.5: Handling code chunks that exceed the embedding
model's maximum token length.

Problem: sentence-transformers silently truncates text longer than
model.max_seq_length -- no error, no warning. For a long function,
this means content near the end is invisibly dropped from the
embedding, causing retrieval to miss it entirely.

Fix: detect over-length chunks and split them into overlapping
token windows, so every part of the function is represented in
at least one embedded window.
"""

from dataclasses import dataclass

from app.embeddings.embedder import _get_model

# Overlap ensures a concept split across a window boundary still
# appears whole in at least one window.
TOKEN_OVERLAP = 50


@dataclass
class TextWindow:
    """One embeddable slice of a (possibly too-long) chunk's source code."""
    text: str
    window_index: int   # 0 for the first window, 1 for the second, etc.
    total_windows: int


def get_token_count(text: str) -> int:
    """Return the real token count for this text, per the model's own tokenizer."""
    model = _get_model()
    tokens = model.tokenizer.encode(text, add_special_tokens=True)
    return len(tokens)


def split_into_windows(text: str) -> list[TextWindow]:
    """
    Split text into one or more windows that each fit within the
    model's max_seq_length, with token-level overlap between windows.

    If the text already fits within the limit, returns a single window
    (no splitting needed -- this is the common case).
    """
    model = _get_model()
    max_tokens = model.max_seq_length
    tokenizer = model.tokenizer

    token_ids = tokenizer.encode(text, add_special_tokens=False)

    if len(token_ids) <= max_tokens:
        return [TextWindow(text=text, window_index=0, total_windows=1)]

    # Split into overlapping windows of token IDs, then decode each
    # window back into text for embedding.
    step = max_tokens - TOKEN_OVERLAP
    raw_windows = [
        token_ids[i:i + max_tokens]
        for i in range(0, len(token_ids), step)
    ]

    windows = []
    for idx, window_ids in enumerate(raw_windows):
        window_text = tokenizer.decode(window_ids, skip_special_tokens=True)
        windows.append(
            TextWindow(text=window_text, window_index=idx, total_windows=len(raw_windows))
        )

    return windows