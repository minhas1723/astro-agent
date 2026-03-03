"""
astro — astronomical & numerological computation for birth chart calculation.

Subpackage providing:
  - Geocoding of birth place to lat/lon (geopy + Nominatim)
  - Sun sign determination from DOB (date-range math)
  - Moon sign + Nakshatra from DOB, birth time, and location (ephem + Lahiri)
  - Numerology (birth number + destiny number from DOB digit sums)
  - All 9 planet sidereal positions + conjunction detection (ephem + Lahiri)

Usage:
    from src.core.astro import geocode_place, get_sun_sign, get_moon_and_nakshatra, get_numerology
    from src.core.astro import get_all_planet_positions, detect_conjunctions
"""

from src.core.astro.geocoder import geocode_place
from src.core.astro.moon import get_moon_and_nakshatra
from src.core.astro.numerology import get_numerology
from src.core.astro.planets import detect_conjunctions, get_all_planet_positions
from src.core.astro.sun_sign import get_sun_sign

__all__ = [
    "detect_conjunctions",
    "geocode_place",
    "get_all_planet_positions",
    "get_moon_and_nakshatra",
    "get_numerology",
    "get_sun_sign",
]
