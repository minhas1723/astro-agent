"""
Agent tools — scoped RAG retrieval tools for RAGAgent.

Each tool retrieves from a specific astrological dimension.
The LLM reads the user's profile from the system context (sun_sign, moon_sign,
nakshatra, etc.) and passes the relevant values as explicit parameters.

Uses src.core.retrieval.search to query the ChromaDB vector store.
"""

from langchain.tools import tool
from src.core.retrieval import search


# ---------------------------------------------------------------------------
# Tool 1 — Sun Sign Context
# ---------------------------------------------------------------------------
@tool
def get_sun_sign_context(sun_sign: str, domain: str) -> str:
    """
    Retrieve personality traits, strengths, challenges, and domain-specific
    guidance for the user's Sun sign.

    Call this for questions about the user's core identity, general character,
    career outlook, love style, or spiritual path.

    Args:
        sun_sign: The user's Sun sign (e.g. 'Scorpio', 'Aries', 'Taurus').
        domain:   One of 'career', 'love', 'spiritual', 'general'.

    Returns:
        Relevant passages grounding the Sun sign in the requested domain.
    """
    domain_query_map = {
        "career": "career profession work tendencies strengths",
        "love": "love relationships romance compatibility",
        "spiritual": "spiritual path soul lesson growth meditation",
        "general": "personality traits challenges strengths character",
    }
    semantic_query = domain_query_map.get(domain, domain)

    # Query A — traits from zodiac_traits.json chunks
    traits = search(
        semantic_query,
        {"zodiac": sun_sign, "topic": domain, "source": "zodiac_traits"},
        n_results=2,
    )

    # Query B — guidance from career/love/spiritual TXT chunks
    guidance = search(
        f"{sun_sign} {semantic_query} advice",
        {"zodiac": sun_sign, "domain": domain, "source": "guidance_txt"},
        n_results=2,
    )

    combined = "\n---\n".join(traits + guidance)
    return f"--- Sun Sign ({sun_sign}) | {domain} ---\n{combined}"


# ---------------------------------------------------------------------------
# Tool 2 — Moon Sign Context
# ---------------------------------------------------------------------------
@tool
def get_moon_sign_context(moon_sign: str, domain: str) -> str:
    """
    Retrieve emotional nature, inner-world patterns, and domain-specific
    guidance for the user's Moon sign.

    Call this when the user asks about emotions, stress, inner life, mental
    peace, mood, or anything related to their emotional self.

    Args:
        moon_sign: The user's Moon sign (e.g. 'Taurus', 'Cancer', 'Pisces').
        domain:    One of 'career', 'love', 'spiritual', 'general'.

    Returns:
        Relevant passages grounding the Moon sign in the requested domain.
    """
    domain_query_map = {
        "career": "emotional stability mental work environment career",
        "love": "emotional love attachment security inner feelings",
        "spiritual": "inner world subconscious spiritual emotional healing",
        "general": "emotions mind mood instincts inner nature",
    }
    semantic_query = domain_query_map.get(domain, domain)

    # Query A — zodiac traits for the Moon sign
    traits = search(
        semantic_query,
        {"zodiac": moon_sign, "topic": domain, "source": "zodiac_traits"},
        n_results=2,
    )

    # Query B — Moon planet's general impact
    moon_impact = search(
        "Moon emotional influence inner world intuition",
        {"planet": "Moon", "source": "planetary_impacts"},
        n_results=1,
    )

    combined = "\n---\n".join(traits + moon_impact)
    return f"--- Moon Sign ({moon_sign}) | {domain} ---\n{combined}"


# ---------------------------------------------------------------------------
# Tool 3 — Nakshatra Context
# ---------------------------------------------------------------------------
@tool
def get_nakshatra_context(nakshatra: str, ruling_planet: str, topic: str) -> str:
    """
    Retrieve Nakshatra-specific insight — personality, career tendencies,
    challenges, spiritual lesson, and mantra.

    Call this when the user asks about their birth star, Nakshatra, lunar
    mansion, or when a deeper reading beyond Sun/Moon sign is needed.

    Args:
        nakshatra:      The user's birth Nakshatra (e.g. 'Rohini', 'Ashwini').
        ruling_planet:  The Nakshatra's ruling planet (e.g. 'Moon', 'Mars').
        topic:          One of 'personality', 'career', 'challenges', 'spiritual'.

    Returns:
        Nakshatra-specific passages plus the ruling planet's general influence.
    """
    topic_query_map = {
        "personality": "personality traits character nature behavior",
        "career": "career profession suitable work tendencies",
        "challenges": "challenges difficulties weaknesses struggles",
        "spiritual": "spiritual lesson soul purpose mantra deity",
    }
    semantic_query = topic_query_map.get(topic, topic)

    # Query A — nakshatra_mapping.json chunks
    nak_results = search(
        semantic_query,
        {"nakshatra": nakshatra, "topic": topic, "source": "nakshatra_mapping"},
        n_results=2,
    )

    # Query B — ruling planet's general impact
    planet_results = search(
        f"{ruling_planet} planet influence characteristics meaning",
        {"planet": ruling_planet, "source": "planetary_impacts"},
        n_results=1,
    )

    combined = "\n---\n".join(nak_results + planet_results)
    return (
        f"--- Nakshatra ({nakshatra}, ruled by {ruling_planet}) | {topic} ---\n"
        f"{combined}"
    )


# ---------------------------------------------------------------------------
# Tool 4 — Planet Context
# ---------------------------------------------------------------------------
@tool
def get_planet_context(planet: str, domain: str) -> str:
    """
    Retrieve the astrological impact of a specific planet in a given life domain.

    Call this ONLY when the user explicitly mentions a planet ('Which planet
    affects my love life?', 'What is Saturn doing to me?'), or when a planet
    is the specific focus of the question.

    Do NOT call this for every question — use Sun/Moon sign tools first.

    Args:
        planet: Planet name. One of: Sun, Moon, Mars, Mercury, Jupiter,
                Saturn, Venus, Rahu, Ketu.
        domain: One of 'career', 'love', 'spiritual', 'general'.

    Returns:
        Planet impact description and domain-specific guidance.
    """
    # Query A — planetary_impacts.json
    planet_results = search(
        f"{planet} represents governs influence impact nature",
        {"planet": planet, "source": "planetary_impacts"},
        n_results=2,
    )

    # Query B — guidance TXT for this planet
    guidance_results = search(
        f"{planet} {domain} advice guidance influence period",
        {"planet": planet, "domain": domain, "source": "guidance_txt"},
        n_results=2,
    )

    combined = "\n---\n".join(planet_results + guidance_results)
    return f"--- Planet ({planet}) | {domain} ---\n{combined}"


# ---------------------------------------------------------------------------
# Tool 5 — House Context
# ---------------------------------------------------------------------------
_LIFE_AREA_TO_HOUSE: dict[str, int] = {
    "self": 1,
    "identity": 1,
    "wealth": 2,
    "speech": 2,
    "communication": 3,
    "siblings": 3,
    "home": 4,
    "mother": 4,
    "creativity": 5,
    "children": 5,
    "romance": 5,
    "health": 6,
    "enemies": 6,
    "marriage": 7,
    "partnership": 7,
    "transformation": 8,
    "secrets": 8,
    "spirituality": 9,
    "luck": 9,
    "philosophy": 9,
    "career": 10,
    "profession": 10,
    "reputation": 10,
    "gains": 11,
    "network": 11,
    "friends": 11,
    "loss": 12,
    "isolation": 12,
    "moksha": 12,
}


@tool
def get_house_context(life_area: str) -> str:
    """
    Retrieve astrological house insight for a given life area.

    Call this when the user's question maps to a specific house:
      career/profession → 10th house
      marriage/partnership → 7th house
      wealth → 2nd house
      health → 6th house
      spirituality/luck/philosophy → 9th house
      creativity/romance/children → 5th house
      home/mother → 4th house
      gains/network → 11th house

    Args:
        life_area: A life topic string, e.g. 'career', 'marriage', 'wealth',
                   'health', 'spirituality', 'home', 'creativity', 'gains'.

    Returns:
        House description and its career/love/spiritual connections.
    """
    house_num = _LIFE_AREA_TO_HOUSE.get(life_area.lower(), 1)

    results = search(
        f"house {house_num} {life_area} represents governs significations",
        {"house_number": house_num, "source": "houses"},
        n_results=1,
    )

    combined = "\n---\n".join(results)
    return f"--- House {house_num} | {life_area} ---\n{combined}"


# ---------------------------------------------------------------------------
# Tool 6 — Numerology Context
# ---------------------------------------------------------------------------
@tool
def get_numerology_context(birth_number: int, destiny_number: int) -> str:
    """
    Retrieve numerological insight based on the user's birth number and
    destiny number.

    Call this when the user asks about numerology, life path number, destiny
    number, or the meaning of numbers in their astrological profile.

    Args:
        birth_number:   The user's birth number (day of birth reduced, 1–9).
        destiny_number: The user's destiny number (full DOB reduced, 1–9).

    Returns:
        Birth number and destiny number meanings from the knowledge base.
    """
    birth_results = search(
        f"birth number {birth_number} meaning traits ruling planet personality",
        {"number": birth_number, "source": "numerology"},
        n_results=1,
    )

    destiny_results = search(
        f"destiny number {destiny_number} life purpose path mission",
        {"number": destiny_number, "source": "numerology"},
        n_results=1,
    )

    combined = "\n---\n".join(birth_results + destiny_results)
    return (
        f"--- Numerology | Birth {birth_number} / Destiny {destiny_number} ---\n"
        f"{combined}"
    )


# ---------------------------------------------------------------------------
# Tool 7 — Conjunction Context
# ---------------------------------------------------------------------------
@tool
def get_conjunction_context(
    planet_1: str, planet_2: str, domain: str = "general"
) -> str:
    """
    Retrieve the astrological meaning of a conjunction (two planets together).

    Call this when the user asks about two planets combining, conjunctions in
    their chart, or the interaction between two planetary energies.

    Args:
        planet_1: First planet name (e.g. 'Sun', 'Mars', 'Rahu').
        planet_2: Second planet name (e.g. 'Moon', 'Saturn', 'Ketu').
        domain:   One of 'career', 'love', 'spiritual', 'general'.

    Returns:
        Conjunction description, traits, and domain-specific implications.
    """
    domain_query_map = {
        "career": "career profession work implication",
        "love": "love relationships romance implication",
        "spiritual": "spiritual growth transformation implication",
        "general": "personality traits positive negative summary",
    }
    semantic_query = domain_query_map.get(domain, domain)

    # Query A — direct conjunction search
    results = search(
        f"{planet_1} {planet_2} conjunction {semantic_query}",
        {"source": "conjunctions"},
        n_results=2,
    )

    # Query B — individual planet impacts for richer context
    p1_impact = search(
        f"{planet_1} influence nature characteristics",
        {"planet": planet_1, "source": "planetary_impacts"},
        n_results=1,
    )

    combined = "\n---\n".join(results + p1_impact)
    return f"--- Conjunction ({planet_1} + {planet_2}) | {domain} ---\n{combined}"


# ---------------------------------------------------------------------------
# Exported tool list — passed to the LangChain agent
# ---------------------------------------------------------------------------
ASTRO_TOOLS = [
    get_sun_sign_context,
    get_moon_sign_context,
    get_nakshatra_context,
    get_planet_context,
    get_house_context,
    get_numerology_context,
    get_conjunction_context,
]
