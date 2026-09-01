"""
Phase 4, Step 1: Persisting embedded windows to Chroma (vector store).

Responsibility: store EmbeddedWindow vectors + metadata in a Chroma
collection, and provide a basic similarity search interface.
"""

import chromadb

from app.embeddings.embedding_pipeline import EmbeddedWindow

COLLECTION_NAME = "code_chunks"
PERSIST_DIR = "./chroma_data"  # embedded mode: stores to local disk


def get_client():
    """Returns a persistent, embedded Chroma client (no server needed yet)."""
    return chromadb.PersistentClient(path=PERSIST_DIR)


def get_collection(client):
    """Get or create the collection used for all code chunk embeddings."""
    return client.get_or_create_collection(name=COLLECTION_NAME)


def add_embeddings(collection, windows: list[EmbeddedWindow]) -> None:
    """
    Store a batch of EmbeddedWindow objects in the Chroma collection.

    Each window gets a unique ID combining its chunk_id and window_index,
    since a single chunk can produce multiple windows.
    """
    ids = [f"{w.chunk_id}_{w.window_index}" for w in windows]
    embeddings = [w.vector for w in windows]
    documents = [w.text for w in windows]
    metadatas = [
        {
            "chunk_id": w.chunk_id,
            "window_index": w.window_index,
            "total_windows": w.total_windows,
            "function_name": w.function_name,
            "class_name": w.class_name or "",  # Chroma metadata can't store None
            "start_line": w.start_line,
            "end_line": w.end_line,
            "language": w.language,
            "repo_id": w.repo_id,
            "file_path": w.file_path,
        }
        for w in windows
    ]

    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)


def search(collection, query_vector: list[float], top_k: int = 5) -> dict:
    """Run a similarity search against the collection."""
    return collection.query(query_embeddings=[query_vector], n_results=top_k)