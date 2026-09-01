"""
Phase 3, Step 1: Code-aware embedding model.

Wraps a sentence-transformers model fine-tuned for code search, so the
rest of the system depends only on this interface -- not on which
specific model or library is used underneath.
"""

from sentence_transformers import SentenceTransformer

MODEL_NAME = "flax-sentence-embeddings/st-codesearch-distilroberta-base"

_model = None  # lazy-loaded singleton, avoids reloading the model on every call


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_text(text: str) -> list[float]:
    """Embed a single piece of text (e.g. one code chunk) into a vector."""
    model = _get_model()
    vector = model.encode(text, convert_to_numpy=True)
    return vector.tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts at once -- more efficient than one-by-one."""
    model = _get_model()
    vectors = model.encode(texts, convert_to_numpy=True, batch_size=16)
    return [v.tolist() for v in vectors]