"""
geocoder — resolve a birth place string to (latitude, longitude).

Uses geopy with OpenStreetMap Nominatim (free, no API key).
Results are cached in-process with lru_cache (sufficient for single-worker uvicorn).
"""

from __future__ import annotations

import logging
from functools import lru_cache

from geopy.geocoders import Nominatim

logger = logging.getLogger(__name__)


@lru_cache(maxsize=256)
def geocode_place(place: str) -> tuple[float, float]:
    """
    Geocode a place name to (latitude, longitude).

    Args:
        place: Human-readable place string, e.g. "Jaipur, India".

    Returns:
        Tuple of (latitude, longitude) as floats.

    Raises:
        ValueError: If the place could not be geocoded.
    """
    geolocator = Nominatim(user_agent="astro_agent")
    location = geolocator.geocode(place, timeout=10)

    if not location:
        msg = f"Could not geocode place: {place!r}"
        raise ValueError(msg)

    logger.info(
        "Geocoded %r → (%.4f, %.4f)",
        place,
        location.latitude,
        location.longitude,
    )
    return location.latitude, location.longitude
