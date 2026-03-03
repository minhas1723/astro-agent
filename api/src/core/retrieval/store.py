"""
store — ChromaDB client and collection management.

Provides access to the persistent ChromaDB collection used for
the astrology knowledge base. Uses local ONNX embeddings (all-MiniLM-L6-v2)
via ChromaDB's built-in embedding function — no API key required.
"""

from __future__ import annotations

import chromadb
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

# ---------------------------------------------------------------------------
# Singleton ChromaDB client + collection
# ---------------------------------------------------------------------------
_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None

COLLECTION_NAME = "astro_knowledge"

# Singleton embedding function (loads ONNX model once)
_embedding_fn: ONNXMiniLM_L6_V2 | None = None


def _get_embedding_fn() -> ONNXMiniLM_L6_V2:
    """Return the local ONNX MiniLM-L6-v2 embedding function."""
    global _embedding_fn  # noqa: PLW0603
    if _embedding_fn is None:
        _embedding_fn = ONNXMiniLM_L6_V2()
    return _embedding_fn


def get_client() -> chromadb.ClientAPI:
    """Return (or create) the persistent ChromaDB client."""
    global _client  # noqa: PLW0603
    if _client is None:
        _client = chromadb.PersistentClient(path="data/chroma_db")
    return _client


def get_collection() -> chromadb.Collection:
    """Return (or create) the astro_knowledge collection with ONNX embeddings."""
    global _collection  # noqa: PLW0603
    if _collection is None:
        client = get_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=_get_embedding_fn(),
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def reset_collection() -> None:
    """Drop and recreate the collection (used during re-indexing)."""
    global _collection  # noqa: PLW0603
    client = get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except ValueError:
        pass  # collection doesn't exist yet
    _collection = None
