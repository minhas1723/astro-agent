"""
search — query wrapper for the astro knowledge ChromaDB collection.

Single entry point used by all tools in src/agent/tools.py.
Handles where-clause construction and returns clean text passages.
"""

from __future__ import annotations

import logging

from chromadb.errors import InvalidArgumentError
from src.core.retrieval.store import get_collection

logger = logging.getLogger(__name__)


def search(
    semantic_query: str,
    filters: dict | None = None,
    n_results: int = 3,
) -> list[str]:
    """
    Query the astro_knowledge collection and return matching text passages.

    Args:
        semantic_query: Text to embed and search semantically against the store.
        filters:        Optional metadata filters. Keys can include:
                        zodiac, planet, nakshatra, house_number, number,
                        domain, topic, source, section, element, etc.
                        Values can be strings, ints, or dicts with ChromaDB
                        operators ($in, $or, etc.).
        n_results:      Maximum number of results to return.

    Returns:
        List of document text strings, ordered by relevance.
    """
    collection = get_collection()

    if collection.count() == 0:
        return ["Knowledge base is empty — please run indexing first."]

    # Build the where clause from filters
    where = _build_where(filters) if filters else None

    try:
        results = collection.query(
            query_texts=[semantic_query],
            where=where,
            n_results=n_results,
        )
    except (InvalidArgumentError, ValueError) as exc:
        # Filter mismatch (e.g. metadata key doesn't exist, type mismatch).
        # Fall back to unfiltered search so the tool still returns *something*,
        # but log the issue so we can fix the filter definition.
        logger.warning(
            "Filtered search failed (query=%r, where=%r): %s — falling back to unfiltered.",
            semantic_query,
            where,
            exc,
        )
        results = collection.query(
            query_texts=[semantic_query],
            n_results=n_results,
        )

    # Extract documents from the results
    documents = results.get("documents", [[]])[0]
    return documents if documents else ["No relevant passages found."]


def _build_where(filters: dict) -> dict | None:
    """
    Build a ChromaDB where clause from a flat dict of filters.

    If multiple filters are provided, they are combined with $and.
    Single filters are passed directly.
    """
    if not filters:
        return None

    conditions = []
    for key, value in filters.items():
        if value is None:
            continue
        if isinstance(value, dict):
            # Already a ChromaDB operator (e.g. {"$in": ["Sun", "Moon"]})
            conditions.append({key: value})
        else:
            conditions.append({key: value})

    if len(conditions) == 0:
        return None
    if len(conditions) == 1:
        return conditions[0]

    return {"$and": conditions}
