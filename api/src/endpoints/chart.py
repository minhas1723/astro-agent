"""
chart — endpoint for computing a birth chart from user details.

Pipeline:
  1. Geocode birth place → (lat, lon)     [geopy / Nominatim]
  2. DOB → Sun sign                       [date-range math]
  3. DOB + time + location → Moon sign    [ephem + Lahiri Ayanamsa]
                            + Nakshatra
  4. DOB → birth number + destiny number  [digit-sum math]
  5. DOB + time + location → all 9 planet positions + conjunctions [ephem + Lahiri]
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.core.astro import (
    detect_conjunctions,
    geocode_place,
    get_all_planet_positions,
    get_moon_and_nakshatra,
    get_numerology,
    get_sun_sign,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ChartRequest(BaseModel):
    name: str
    email: str
    dob: str  # ISO date  e.g. "1995-11-04"
    birth_time: str  # "HH:mm" or "" if unknown
    birth_place: str


class ConjunctionInfo(BaseModel):
    planets: list[str]
    sign: str


class ChartResponse(BaseModel):
    sun_sign: str
    moon_sign: str
    nakshatra: str
    birth_number: int
    destiny_number: int
    planetary_positions: dict[str, str]  # planet → sidereal sign
    conjunctions: list[ConjunctionInfo]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.post("/calculate", response_model=ChartResponse)
async def calculate_chart(req: ChartRequest) -> ChartResponse:
    """
    Compute a birth chart from user details.

    Steps:
      1. Geocode birth place to (lat, lon).
      2. Determine Sun sign from DOB.
      3. Compute Moon sign and Nakshatra using ephem + Lahiri Ayanamsa.
      4. Calculate birth number and destiny number from DOB.
      5. Compute all 9 planet sidereal positions and detect conjunctions.
    """
    logger.info(
        "Chart calculation requested for %s (dob=%s, place=%s)",
        req.name,
        req.dob,
        req.birth_place,
    )

    # 1. Geocode birth place
    try:
        lat, lon = geocode_place(req.birth_place)
    except ValueError as exc:
        logger.warning("Geocoding failed for %r: %s", req.birth_place, exc)
        raise HTTPException(
            status_code=422,
            detail=f"Could not locate place: {req.birth_place!r}. Please try a more specific name.",
        ) from exc

    # 2. Sun sign (pure date math)
    sun_sign = get_sun_sign(req.dob)

    # 3. Moon sign + Nakshatra (ephem + Lahiri)
    birth_time = req.birth_time if req.birth_time else "12:00"
    moon_sign, nakshatra = get_moon_and_nakshatra(req.dob, birth_time, lat, lon)

    # 4. Numerology (pure math)
    birth_number, destiny_number = get_numerology(req.dob)

    # 5. All planet positions + conjunctions
    positions = get_all_planet_positions(req.dob, birth_time, lat, lon)
    conj_list = detect_conjunctions(positions)

    # Simplify positions to planet → sign for the response
    planetary_positions = {planet: data["sign"] for planet, data in positions.items()}

    logger.info(
        "Chart for %s: sun=%s moon=%s nak=%s birth#=%d destiny#=%d planets=%s conj=%s",
        req.name,
        sun_sign,
        moon_sign,
        nakshatra,
        birth_number,
        destiny_number,
        planetary_positions,
        [f"{c['planets'][0]}+{c['planets'][1]}" for c in conj_list],
    )

    return ChartResponse(
        sun_sign=sun_sign,
        moon_sign=moon_sign,
        nakshatra=nakshatra,
        birth_number=birth_number,
        destiny_number=destiny_number,
        planetary_positions=planetary_positions,
        conjunctions=[ConjunctionInfo(**c) for c in conj_list],
    )
