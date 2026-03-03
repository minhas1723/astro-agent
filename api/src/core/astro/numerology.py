"""
numerology — compute birth number and destiny number from DOB.

Pure digit-sum arithmetic, no external dependencies.

  Birth number:   Day of birth reduced to a single digit (1-9).
  Destiny number: All digits of the full DOB summed and reduced to a single digit.
"""

from __future__ import annotations

from datetime import date


def _reduce_to_single_digit(n: int) -> int:
    """Repeatedly sum digits until a single digit (1-9) remains."""
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def get_numerology(dob: str) -> tuple[int, int]:
    """
    Compute birth number and destiny number from date of birth.

    Args:
        dob: ISO date string, e.g. "1995-11-04".

    Returns:
        Tuple of (birth_number, destiny_number), each 1-9.

    Examples:
        >>> get_numerology("1995-11-04")
        (4, 3)
        # birth_number:  04 → 0+4 = 4
        # destiny_number: 1+9+9+5+1+1+0+4 = 30 → 3+0 = 3
    """
    d = date.fromisoformat(dob)

    # Birth number: reduce the day
    birth_number = _reduce_to_single_digit(d.day)

    # Destiny number: sum all digits of YYYYMMDD
    all_digits_sum = sum(int(c) for c in dob.replace("-", ""))
    destiny_number = _reduce_to_single_digit(all_digits_sum)

    return birth_number, destiny_number
