"""
indexer — loads all data files, routes to chunkers, and bulk-adds to ChromaDB.

Call `index_all(data_dir)` once at application startup to populate the store.
It is idempotent: if the collection already contains documents, it skips.
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.core.retrieval.chunkers import (
    chunk_conjunctions,
    chunk_guidance_txt,
    chunk_houses,
    chunk_nakshatras,
    chunk_numerology,
    chunk_planetary_impacts,
    chunk_zodiac_traits,
)
from src.core.retrieval.store import get_collection, reset_collection

logger = logging.getLogger(__name__)

# Max batch size for ChromaDB upsert (API limit is ~5461 with embeddings)
_BATCH_SIZE = 100


def index_all(data_dir: str | Path, *, force: bool = False) -> int:
    """
    Index all data files from the given directory into ChromaDB.

    Args:
        data_dir:  Path to the data/ folder.
        force:     If True, drop and rebuild the index. Otherwise skip if
                   the collection already has documents.

    Returns:
        Total number of documents indexed.
    """
    data_path = Path(data_dir)

    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_path}")

    collection = get_collection()

    # Skip if already indexed (unless forced)
    if not force and collection.count() > 0:
        existing = collection.count()
        logger.info(f"Collection already has {existing} documents — skipping indexing.")
        return existing

    if force:
        logger.info("Force re-indexing — dropping existing collection.")
        reset_collection()
        collection = get_collection()

    # Route each file to its chunker
    all_docs = []

    # JSON files
    _route_json(data_path, all_docs)

    # TXT guidance files
    _route_txt(data_path, all_docs)

    if not all_docs:
        logger.warning("No documents generated from data files.")
        return 0

    # Batch upsert into ChromaDB
    total = len(all_docs)
    logger.info(f"Indexing {total} documents into ChromaDB...")

    for i in range(0, total, _BATCH_SIZE):
        batch = all_docs[i : i + _BATCH_SIZE]
        collection.add(
            ids=[d["id"] for d in batch],
            documents=[d["text"] for d in batch],
            metadatas=[d["metadata"] for d in batch],
        )
        logger.info(f"  Batch {i // _BATCH_SIZE + 1}: {len(batch)} docs added.")

    final_count = collection.count()
    logger.info(f"Indexing complete. Total documents in collection: {final_count}")
    return final_count


def _route_json(data_path: Path, all_docs: list) -> None:
    """Route JSON files to their respective chunkers."""
    json_chunkers = {
        "zodiac_traits.json": chunk_zodiac_traits,
        "planetary_impacts.json": chunk_planetary_impacts,
        "nakshatra_mapping.json": chunk_nakshatras,
        "houses.json": chunk_houses,
        "conjunctions.json": chunk_conjunctions,
        "numerology.json": chunk_numerology,
    }

    for filename, chunker in json_chunkers.items():
        filepath = data_path / filename
        if filepath.exists():
            docs = chunker(filepath)
            all_docs.extend(docs)
            logger.info(f"  {filename}: {len(docs)} chunks")
        else:
            logger.warning(f"  {filename}: NOT FOUND — skipped")


def _route_txt(data_path: Path, all_docs: list) -> None:
    """Route TXT guidance files to the guidance chunker."""
    txt_files = {
        "career_guidance.txt": "career",
        "love_guidance.txt": "love",
        "spiritual_guidance.txt": "spiritual",
    }

    for filename, domain in txt_files.items():
        filepath = data_path / filename
        if filepath.exists():
            docs = chunk_guidance_txt(filepath, domain)
            all_docs.extend(docs)
            logger.info(f"  {filename}: {len(docs)} chunks")
        else:
            logger.warning(f"  {filename}: NOT FOUND — skipped")
