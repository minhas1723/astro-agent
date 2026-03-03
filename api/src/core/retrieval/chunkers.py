"""
chunkers — file-specific chunking functions for the RAG knowledge base.

Each data file has a dedicated chunker that:
  1. Parses the raw file content
  2. Splits it into semantically meaningful chunks
  3. Attaches metadata for filtering (zodiac, planet, topic, domain, etc.)

Every chunker returns a list of dicts: {"id": str, "text": str, "metadata": dict}
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TypedDict


class Document(TypedDict):
    id: str
    text: str
    metadata: dict


# ---------------------------------------------------------------------------
# zodiac_traits.json → one doc per (sign × topic)
# ---------------------------------------------------------------------------

# Topics we want to split each sign entry into
_ZODIAC_TOPIC_FIELDS: dict[str, list[str]] = {
    "personality": ["personality_traits", "element", "ruling_planet", "modality"],
    "career": ["career_tendencies"],
    "love": ["love_style", "compatible_planets"],
    "challenges": ["challenges"],
    "spiritual": ["spiritual_nature"],
}


def chunk_zodiac_traits(path: Path) -> list[Document]:
    """Chunk zodiac_traits.json into per-sign, per-topic documents."""
    data = json.loads(path.read_text())
    docs: list[Document] = []

    for sign_key, sign_data in data.items():
        sign_name = sign_data.get("sign", sign_key)

        for topic, fields in _ZODIAC_TOPIC_FIELDS.items():
            parts: list[str] = [f"{sign_name} — {topic}:"]

            for field in fields:
                value = sign_data.get(field)
                if value is None:
                    continue

                label = field.replace("_", " ").title()
                if isinstance(value, list):
                    parts.append(f"{label}: {', '.join(str(v) for v in value)}")
                else:
                    parts.append(f"{label}: {value}")

            # Also include strengths in personality chunk
            if topic == "personality":
                strengths = sign_data.get("strengths")
                if strengths and isinstance(strengths, list):
                    parts.append(f"Strengths: {', '.join(strengths)}")

            text = "\n".join(parts)
            doc_id = f"zodiac_{sign_name.lower()}_{topic}"

            docs.append(
                {
                    "id": doc_id,
                    "text": text,
                    "metadata": {
                        "zodiac": sign_name,
                        "topic": topic,
                        "source": "zodiac_traits",
                    },
                }
            )

    return docs


# ---------------------------------------------------------------------------
# planetary_impacts.json → one doc per (planet × topic)
# ---------------------------------------------------------------------------

_PLANET_TOPIC_FIELDS: dict[str, list[str]] = {
    "general": ["description", "nature", "symbolism"],
    "career": ["career_impact"],
    "love": ["love_impact"],
    "spiritual": ["spiritual_impact"],
}


def chunk_planetary_impacts(path: Path) -> list[Document]:
    """Chunk planetary_impacts.json into per-planet, per-topic documents."""
    data = json.loads(path.read_text())
    docs: list[Document] = []

    for planet_key, planet_data in data.items():
        planet_name = planet_data.get("planet", planet_key)

        for topic, fields in _PLANET_TOPIC_FIELDS.items():
            parts: list[str] = [f"Planet {planet_name} — {topic}:"]

            for field in fields:
                value = planet_data.get(field)
                if value is None:
                    continue

                label = field.replace("_", " ").title()
                if isinstance(value, list):
                    parts.append(f"{label}: {', '.join(str(v) for v in value)}")
                elif isinstance(value, dict):
                    for sub_key, sub_val in value.items():
                        parts.append(f"  {sub_key}: {sub_val}")
                else:
                    parts.append(f"{label}: {value}")

            # Add keywords if available
            keywords = planet_data.get("keywords")
            if keywords and isinstance(keywords, list):
                parts.append(f"Keywords: {', '.join(keywords)}")

            text = "\n".join(parts)
            doc_id = f"planet_{planet_name.lower().replace(' ', '_')}_{topic}"

            docs.append(
                {
                    "id": doc_id,
                    "text": text,
                    "metadata": {
                        "planet": planet_name,
                        "topic": topic,
                        "source": "planetary_impacts",
                    },
                }
            )

    return docs


# ---------------------------------------------------------------------------
# nakshatra_mapping.json → one doc per (nakshatra × topic)
# ---------------------------------------------------------------------------

_NAKSHATRA_TOPIC_FIELDS: dict[str, list[str]] = {
    "personality": [
        "personality_traits",
        "strengths",
        "symbol",
        "deity",
        "element",
        "guna",
    ],
    "career": ["career_associations"],
    "challenges": ["challenges"],
    "spiritual": ["spiritual_lesson"],
}


def chunk_nakshatras(path: Path) -> list[Document]:
    """Chunk nakshatra_mapping.json into per-nakshatra, per-topic documents."""
    data = json.loads(path.read_text())
    docs: list[Document] = []

    for nak_key, nak_data in data.items():
        nak_name = nak_data.get("nakshatra", nak_key)
        ruling_planet = nak_data.get("ruling_planet", "unknown")
        zodiac_span = nak_data.get("zodiac_span", "unknown")

        for topic, fields in _NAKSHATRA_TOPIC_FIELDS.items():
            parts: list[str] = [
                f"Nakshatra {nak_name} (ruled by {ruling_planet}, "
                f"spans {zodiac_span}) — {topic}:"
            ]

            for field in fields:
                value = nak_data.get(field)
                if value is None:
                    continue

                label = field.replace("_", " ").title()
                if isinstance(value, list):
                    parts.append(f"{label}: {', '.join(str(v) for v in value)}")
                else:
                    parts.append(f"{label}: {value}")

            text = "\n".join(parts)
            doc_id = f"nakshatra_{nak_name.lower().replace(' ', '_')}_{topic}"

            docs.append(
                {
                    "id": doc_id,
                    "text": text,
                    "metadata": {
                        "nakshatra": nak_name,
                        "ruling_planet": ruling_planet,
                        "zodiac_span": zodiac_span,
                        "topic": topic,
                        "source": "nakshatra_mapping",
                    },
                }
            )

    return docs


# ---------------------------------------------------------------------------
# houses.json → one doc per house (flat array)
# ---------------------------------------------------------------------------


def chunk_houses(path: Path) -> list[Document]:
    """Chunk houses.json — one doc per house with all its connections."""
    data = json.loads(path.read_text())
    docs: list[Document] = []

    for house in data:
        house_num = house["house_number"]
        name = house.get("name", f"House {house_num}")

        parts = [
            f"{name} (House {house_num}):",
            f"Type: {house.get('type', 'N/A')}",
            f"Represents: {house.get('represents', 'N/A')}",
        ]

        significations = house.get("significations", [])
        if significations:
            parts.append(f"Significations: {', '.join(significations)}")

        for connection in (
            "career_connection",
            "love_connection",
            "spiritual_connection",
        ):
            value = house.get(connection)
            if value:
                label = connection.replace("_", " ").title()
                parts.append(f"{label}: {value}")

        keywords = house.get("keywords", [])
        if keywords:
            parts.append(f"Keywords: {', '.join(keywords)}")

        text = "\n".join(parts)
        doc_id = f"house_{house_num}"

        docs.append(
            {
                "id": doc_id,
                "text": text,
                "metadata": {
                    "house_number": house_num,
                    "source": "houses",
                },
            }
        )

    return docs


# ---------------------------------------------------------------------------
# conjunctions.json → one doc per conjunction (flat array)
# ---------------------------------------------------------------------------


def chunk_conjunctions(path: Path) -> list[Document]:
    """Chunk conjunctions.json — one doc per planetary conjunction."""
    data = json.loads(path.read_text())
    docs: list[Document] = []

    for conj in data:
        planets = conj.get("planets", [])
        planets_str = " + ".join(planets)
        conj_type = conj.get("type", "N/A")

        parts = [
            f"Conjunction: {planets_str} ({conj_type})",
            f"Summary: {conj.get('summary', '')}",
        ]

        for trait_key in ("positive_traits", "negative_traits"):
            traits = conj.get(trait_key, [])
            if traits:
                label = trait_key.replace("_", " ").title()
                parts.append(f"{label}:")
                for t in traits:
                    parts.append(f"  - {t}")

        for field in (
            "career_implication",
            "love_implication",
            "spiritual_implication",
        ):
            value = conj.get(field)
            if value:
                label = field.replace("_", " ").title()
                parts.append(f"{label}: {value}")

        keywords = conj.get("keywords", [])
        if keywords:
            parts.append(f"Keywords: {', '.join(keywords)}")

        text = "\n".join(parts)
        # Use sorted planet names to create a stable ID
        sorted_planets = "_".join(sorted(p.lower() for p in planets))
        doc_id = f"conjunction_{sorted_planets}"

        docs.append(
            {
                "id": doc_id,
                "text": text,
                "metadata": {
                    "planets": planets_str,
                    "conjunction_type": conj_type,
                    "source": "conjunctions",
                },
            }
        )

    return docs


# ---------------------------------------------------------------------------
# numerology.json → one doc per number (flat array)
# ---------------------------------------------------------------------------


def chunk_numerology(path: Path) -> list[Document]:
    """Chunk numerology.json — one doc per number with all its meanings."""
    data = json.loads(path.read_text())
    docs: list[Document] = []

    for entry in data:
        number = entry["number"]
        ruling = entry.get("ruling_planet", "N/A")

        parts = [
            f"Number {number} (ruled by {ruling}):",
            f"Birth Number Meaning: {entry.get('birth_number_meaning', '')}",
            f"Destiny Number Meaning: {entry.get('destiny_number_meaning', '')}",
        ]

        for trait_key in ("positive_traits", "negative_traits"):
            traits = entry.get(trait_key, [])
            if traits:
                label = trait_key.replace("_", " ").title()
                parts.append(f"{label}: {', '.join(traits)}")

        for field in ("career_alignment", "love_alignment", "spiritual_alignment"):
            value = entry.get(field)
            if value:
                label = field.replace("_", " ").title()
                parts.append(f"{label}: {value}")

        compat = entry.get("compatible_numbers", [])
        incompat = entry.get("incompatible_numbers", [])
        if compat:
            parts.append(f"Compatible Numbers: {', '.join(str(n) for n in compat)}")
        if incompat:
            parts.append(f"Incompatible Numbers: {', '.join(str(n) for n in incompat)}")

        keywords = entry.get("keywords", [])
        if keywords:
            parts.append(f"Keywords: {', '.join(keywords)}")

        text = "\n".join(parts)
        doc_id = f"numerology_{number}"

        docs.append(
            {
                "id": doc_id,
                "text": text,
                "metadata": {
                    "number": number,
                    "source": "numerology",
                },
            }
        )

    return docs


# ---------------------------------------------------------------------------
# *_guidance.txt → one doc per [SECTION]
# ---------------------------------------------------------------------------

# Tags in the TXT files and their metadata mapping
_TAG_PATTERNS = {
    "PLANET_": "planet",  # [PLANET_SUN] → planet = "Sun"
    "ELEMENT_": "element",  # [ELEMENT_FIRE] → element = "Fire"
    "NAKSHATRA_": "nakshatra",  # [NAKSHATRA_ASHWINI] → nakshatra = "Ashwini"
}

# All 12 zodiac signs to identify zodiac tags like [ARIES], [TAURUS]
_ZODIAC_SIGNS = {
    "ARIES",
    "TAURUS",
    "GEMINI",
    "CANCER",
    "LEO",
    "VIRGO",
    "LIBRA",
    "SCORPIO",
    "SAGITTARIUS",
    "CAPRICORN",
    "AQUARIUS",
    "PISCES",
}


def chunk_guidance_txt(path: Path, domain: str) -> list[Document]:
    """
    Chunk a guidance TXT file (career/love/spiritual) by [SECTION] tags.

    Each [SECTION] block becomes one document with metadata identifying:
      - domain (career / love / spiritual)
      - zodiac, planet, element, or nakshatra depending on the tag
    """
    content = path.read_text()
    docs: list[Document] = []

    # Find all sections: [TAG] followed by lines until the next [TAG] or EOF
    section_pattern = re.compile(r"\[([A-Z_]+)\]\s*\n(.*?)(?=\n\[|$)", re.DOTALL)

    for match in section_pattern.finditer(content):
        tag = match.group(1)
        body = match.group(2).strip()

        if not body:
            continue

        # Determine what kind of entity this tag represents
        metadata: dict = {"domain": domain, "source": "guidance_txt"}

        if tag == "GENERAL":
            metadata["section"] = "general"
        elif tag in _ZODIAC_SIGNS:
            metadata["zodiac"] = tag.title()
        else:
            # Check prefixed tags: PLANET_SUN, ELEMENT_FIRE, NAKSHATRA_ASHWINI
            matched = False
            for prefix, meta_key in _TAG_PATTERNS.items():
                if tag.startswith(prefix):
                    entity_name = tag[len(prefix) :].title()
                    metadata[meta_key] = entity_name
                    matched = True
                    break

            if not matched:
                metadata["section"] = tag.lower()

        # Build readable text
        text = f"[{domain.upper()}] {tag.replace('_', ' ').title()}:\n{body}"
        doc_id = f"guidance_{domain}_{tag.lower()}"

        docs.append(
            {
                "id": doc_id,
                "text": text,
                "metadata": metadata,
            }
        )

    return docs
