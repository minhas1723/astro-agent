"""
planets — compute sidereal positions for all 9 Vedic planets and detect conjunctions.

Pipeline:
  1. ephem computes tropical ecliptic longitudes for Sun, Moon, Mars, Mercury,
     Jupiter, Venus, Saturn.
  2. Rahu/Ketu are derived from the Moon's ascending/descending node.
  3. Subtract Lahiri Ayanamsa to get sidereal longitudes.
  4. Determine sidereal sign for each planet.
  5. Detect conjunctions: two planets in the same sidereal sign.
"""

from __future__ import annotations

import logging
import math

import ephem
from src.core.astro.moon import _SIDEREAL_SIGNS, _lahiri_ayanamsa

logger = logging.getLogger(__name__)

# Mapping of planet name → ephem body constructor
_EPHEM_BODIES: dict[str, type] = {
    "Sun": ephem.Sun,
    "Moon": ephem.Moon,
    "Mars": ephem.Mars,
    "Mercury": ephem.Mercury,
    "Jupiter": ephem.Jupiter,
    "Venus": ephem.Venus,
    "Saturn": ephem.Saturn,
}


def _sidereal_lon(body: ephem.Body, observer: ephem.Observer, ayanamsa: float) -> float:
    """Compute sidereal ecliptic longitude in degrees for an ephem body."""
    body.compute(observer)
    ecl = ephem.Ecliptic(body, epoch=observer.date)
    tropical_lon = math.degrees(float(ecl.lon))
    return (tropical_lon - ayanamsa) % 360


def get_all_planet_positions(
    dob: str,
    birth_time: str,
    lat: float,
    lon: float,
) -> dict[str, dict]:
    """
    Compute sidereal positions for all 9 Vedic planets.

    Args:
        dob:        ISO date string, e.g. "1995-11-04".
        birth_time: Time in "HH:MM" 24-hour format, or "" for unknown.
        lat:        Latitude of birth place.
        lon:        Longitude of birth place.

    Returns:
        Dict mapping planet name → {"longitude": float, "sign": str}
    """
    if not birth_time or not birth_time.strip():
        birth_time = "12:00"

    observer = ephem.Observer()
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.date = f"{dob} {birth_time}"

    year = int(dob[:4])
    ayanamsa = _lahiri_ayanamsa(year)

    positions: dict[str, dict] = {}

    # Compute the 7 visible planets
    for name, body_cls in _EPHEM_BODIES.items():
        body = body_cls()
        sid_lon = _sidereal_lon(body, observer, ayanamsa)
        sign_index = int(sid_lon / 30)
        positions[name] = {
            "longitude": round(sid_lon, 2),
            "sign": _SIDEREAL_SIGNS[sign_index],
        }

    # Compute Rahu (mean ascending lunar node) and Ketu (opposite)
    # Use the Meeus mean lunar node formula.
    # ephem gives the ascending node's RA/Dec through Moon.hlat, but the
    # standard way is to use the fixed-body "Node" computation.
    # The Moon's ascending node longitude can be obtained via libastro.
    # A simpler (standard Jyotish) approach: compute from ephem's Moon object.
    #
    # ephem doesn't directly expose the lunar node longitude, so we use
    # the formula: Rahu ≈ mean node position from the observer's date.
    # The mean node regresses ~19.355° per year from a known epoch.
    #
    # Reference epoch: Rahu was at 0° (0° Aries tropical) on ~Jan 19, 1934.
    # Mean regression rate: 19.35506 degrees/year (360° / 18.6134 year cycle).

    jd = float(observer.date) + 2415020.0  # ephem uses Dublin JD; convert to JD
    # Julian centuries from J2000.0
    t_centuries = (jd - 2451545.0) / 36525.0
    # Mean longitude of ascending node (Meeus, "Astronomical Algorithms")
    rahu_tropical = (
        125.04452
        - 1934.136261 * t_centuries
        + 0.0020708 * t_centuries * t_centuries
        + t_centuries * t_centuries * t_centuries / 450000.0
    ) % 360

    rahu_sidereal = (rahu_tropical - ayanamsa) % 360
    ketu_sidereal = (rahu_sidereal + 180) % 360

    rahu_sign_index = int(rahu_sidereal / 30)
    ketu_sign_index = int(ketu_sidereal / 30)

    positions["Rahu"] = {
        "longitude": round(rahu_sidereal, 2),
        "sign": _SIDEREAL_SIGNS[rahu_sign_index],
    }
    positions["Ketu"] = {
        "longitude": round(ketu_sidereal, 2),
        "sign": _SIDEREAL_SIGNS[ketu_sign_index],
    }

    logger.info(
        "Planet positions computed: %s",
        ", ".join(f"{p}={d['sign']}" for p, d in positions.items()),
    )

    return positions


def detect_conjunctions(positions: dict[str, dict]) -> list[dict]:
    """
    Detect conjunctions: two planets in the same sidereal sign.

    Args:
        positions: Output of get_all_planet_positions().

    Returns:
        List of {"planets": [p1, p2], "sign": str} for each conjunction found.
    """
    # Group planets by sign
    sign_groups: dict[str, list[str]] = {}
    for planet, data in positions.items():
        sign = data["sign"]
        sign_groups.setdefault(sign, []).append(planet)

    conjunctions: list[dict] = []
    for sign, planets in sign_groups.items():
        if len(planets) < 2:
            continue
        # Generate all unique pairs
        for i in range(len(planets)):
            for j in range(i + 1, len(planets)):
                conjunctions.append(
                    {
                        "planets": sorted([planets[i], planets[j]]),
                        "sign": sign,
                    }
                )

    if conjunctions:
        logger.info(
            "Conjunctions detected: %s",
            ", ".join(
                f"{c['planets'][0]}+{c['planets'][1]} in {c['sign']}"
                for c in conjunctions
            ),
        )
    else:
        logger.info("No conjunctions detected.")

    return conjunctions
