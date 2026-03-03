"""
sun_sign — determine the Western/Tropical Sun sign from a date of birth.

Pure date-range math, no external dependencies.
Sign names match the keys in data/zodiac_traits.json exactly.
"""

from __future__ import annotations

from datetime import date

# (start_month, start_day, end_month, end_day, sign_name)
# Ordered so that a linear scan finds the correct sign.
_ZODIAC_BOUNDARIES: list[tuple[int, int, int, int, str]] = [
    (1, 20, 2, 18, "Aquarius"),
    (2, 19, 3, 20, "Pisces"),
    (3, 21, 4, 19, "Aries"),
    (4, 20, 5, 20, "Taurus"),
    (5, 21, 6, 20, "Gemini"),
    (6, 21, 7, 22, "Cancer"),
    (7, 23, 8, 22, "Leo"),
    (8, 23, 9, 22, "Virgo"),
    (9, 23, 10, 22, "Libra"),
    (10, 23, 11, 21, "Scorpio"),
    (11, 22, 12, 21, "Sagittarius"),
    (12, 22, 1, 19, "Capricorn"),
]


def get_sun_sign(dob: str) -> str:
    """
    Determine the Sun sign (tropical zodiac) from an ISO date string.

    Args:
        dob: Date of birth as ISO-8601 string, e.g. "1995-11-04".

    Returns:
        Zodiac sign name matching data/zodiac_traits.json keys,
        e.g. "Scorpio", "Aries", "Pisces".
    """
    d = date.fromisoformat(dob)
    month, day = d.month, d.day

    for start_m, start_d, end_m, end_d, sign in _ZODIAC_BOUNDARIES:
        if start_m <= end_m:
            # Normal range (same year)
            if (month == start_m and day >= start_d) or (
                month == end_m and day <= end_d
            ):
                return sign
            if start_m < month < end_m:
                return sign
        else:
            # Capricorn wraps around year boundary (Dec 22 → Jan 19)
            if (month == start_m and day >= start_d) or (
                month == end_m and day <= end_d
            ):
                return sign

    # Should never reach here, but default to Capricorn for safety
    return "Capricorn"
