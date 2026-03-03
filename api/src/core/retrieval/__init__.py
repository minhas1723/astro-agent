"""
retrieval — astrology knowledge RAG pipeline.

Subpackage providing:
  - Chunking & indexing of data files into ChromaDB (init_store)
  - Semantic search with metadata filtering (search)

Usage:
    from src.core.retrieval import init_store, search

    # At startup — index all data files
    count = init_store("data/")

    # At runtime — query from tools
    results = search("career strengths", {"zodiac": "Scorpio", "topic": "career"})
"""

from src.core.retrieval.indexer import index_all
from src.core.retrieval.search import search


def init_store(data_dir: str = "data/", *, force: bool = False) -> int:
    """
    Initialize the RAG knowledge store by indexing all data files.

    Args:
        data_dir: Path to the data/ directory.
        force:    If True, re-index even if documents already exist.

    Returns:
        Total number of documents in the collection after indexing.
    """
    return index_all(data_dir, force=force)


__all__ = ["init_store", "search"]
