"""
moon — compute Moon sign (rashi) and Nakshatra from birth details.

Pipeline:
  1. ephem computes the Moon's tropical ecliptic longitude.
  2. Subtract the Lahiri Ayanamsa to get sidereal longitude.
  3. Divide by 30° → Moon sign (rashi) index.
  4. Divide by 13.333° → Nakshatra index.

Nakshatra names match data/nakshatra_mapping.json keys exactly
(including underscores for compound names like "Purva_Phalguni").
"""

from __future__ import annotations

import logging
import math

import ephem

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sidereal zodiac signs (same order as in Vedic astrology — Mesha → Meena)
# Names match data/zodiac_traits.json keys.
# ---------------------------------------------------------------------------
_SIDEREAL_SIGNS: list[str] = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

# ---------------------------------------------------------------------------
# 27 Nakshatras — names match data/nakshatra_mapping.json keys EXACTLY.
# Compound names use underscores (e.g. "Purva_Phalguni").
# ---------------------------------------------------------------------------
NAKSHATRAS: list[str] = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva_Phalguni",
    "Uttara_Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva_Ashadha",
    "Uttara_Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva_Bhadrapada",
    "Uttara_Bhadrapada",
    "Revati",
]


def _lahiri_ayanamsa(year: int) -> float:
    """
    Approximate Lahiri Ayanamsa for a given year.

    Linear approximation accurate to ~+-0.05 deg for years 1950-2030.
    Reference: Lahiri Ayanamsa was 23.685° in 1980 and precesses
    at ~50.3 arcseconds/year (approx 0.01396 deg/year).
    """
    return 23.685 + 0.01396 * (year - 1980)


def get_moon_and_nakshatra(
    dob: str,
    birth_time: str,
    lat: float,
    lon: float,
) -> tuple[str, str]:
    """
    Compute the sidereal Moon sign and Nakshatra.

    Args:
        dob:        ISO date string, e.g. "1995-11-04".
        birth_time: Time in "HH:MM" 24-hour format, or "" for unknown.
                    If empty, defaults to "12:00" (noon — standard practice).
        lat:        Latitude of birth place.
        lon:        Longitude of birth place.

    Returns:
        Tuple of (moon_sign, nakshatra) where both strings match
        data file keys exactly.
    """
    # Default to noon if birth time is unknown
    if not birth_time or not birth_time.strip():
        birth_time = "12:00"

    # Set up the observer
    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    # ephem expects "YYYY/MM/DD HH:MM:SS" or "YYYY-MM-DD HH:MM" format
    observer.date = f"{dob} {birth_time}"

    # Compute the Moon's position
    moon = ephem.Moon(observer)
    ecl = ephem.Ecliptic(moon, epoch=observer.date)

    # Tropical ecliptic longitude in degrees
    tropical_lon = math.degrees(float(ecl.lon))

    # Apply Lahiri Ayanamsa to convert to sidereal
    year = int(dob[:4])
    ayanamsa = _lahiri_ayanamsa(year)
    sidereal_lon = (tropical_lon - ayanamsa) % 360

    # Moon sign: 12 signs x 30 deg each
    sign_index = int(sidereal_lon / 30)
    moon_sign = _SIDEREAL_SIGNS[sign_index]

    # Nakshatra: 27 nakshatras x 13.333 deg each
    nakshatra_span = 360 / 27  # 13.3333...
    nakshatra_index = int(sidereal_lon / nakshatra_span)
    nakshatra = NAKSHATRAS[nakshatra_index]

    logger.info(
        "Moon calc: tropical=%.2f° ayanamsa=%.3f° sidereal=%.2f° → %s / %s",
        tropical_lon,
        ayanamsa,
        sidereal_lon,
        moon_sign,
        nakshatra,
    )

    return moon_sign, nakshatra
