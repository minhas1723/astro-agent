"""
Test script for the astro-agent retrieval pipeline.

Tests three layers:
  1. Chunkers   — all data files parse correctly, producing well-formed docs
  2. Indexing   — ChromaDB store is populated via the new text-embedding-004 model
  3. Search     — semantic queries return relevant results, filters work
"""

import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
log = logging.getLogger("test_retrieval")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# ── helpers ──────────────────────────────────────────────────────────────────

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
WARN = "\033[93m⚠\033[0m"
BOLD = "\033[1m"
RESET = "\033[0m"

failures: list[str] = []


def check(label: str, condition: bool, detail: str = ""):
    if condition:
        print(f"  {PASS}  {label}")
    else:
        msg = f"{label}: {detail}" if detail else label
        print(f"  {FAIL}  {msg}")
        failures.append(msg)


def section(title: str):
    print(f"\n{BOLD}{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}{RESET}")


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 1 — Chunkers (offline, no API calls)
# ═══════════════════════════════════════════════════════════════════════════

section("PHASE 1 · Chunker Validation (no API calls)")

from src.core.retrieval.chunkers import (
    chunk_conjunctions,
    chunk_guidance_txt,
    chunk_houses,
    chunk_nakshatras,
    chunk_numerology,
    chunk_planetary_impacts,
    chunk_zodiac_traits,
)

# ── zodiac_traits.json ───────────────────────────────────────────────────
zodiac_docs = chunk_zodiac_traits(DATA_DIR / "zodiac_traits.json")
check("zodiac_traits: produces docs", len(zodiac_docs) > 0, f"got {len(zodiac_docs)}")
check(
    "zodiac_traits: 5 topics per sign → 60 docs expected (12×5)",
    len(zodiac_docs) == 60,
    f"got {len(zodiac_docs)}",
)
# spot-check structure
sample = zodiac_docs[0]
check("zodiac_traits: doc has 'id'", "id" in sample)
check("zodiac_traits: doc has 'text'", "text" in sample and len(sample["text"]) > 10)
check("zodiac_traits: metadata has 'zodiac'", "zodiac" in sample["metadata"])
check("zodiac_traits: metadata has 'topic'", "topic" in sample["metadata"])
check(
    "zodiac_traits: metadata has 'source'",
    sample["metadata"].get("source") == "zodiac_traits",
)

# ── planetary_impacts.json ───────────────────────────────────────────────
planet_docs = chunk_planetary_impacts(DATA_DIR / "planetary_impacts.json")
check(
    "planetary_impacts: produces docs", len(planet_docs) > 0, f"got {len(planet_docs)}"
)
check(
    "planetary_impacts: metadata has 'planet'", "planet" in planet_docs[0]["metadata"]
)

# ── nakshatra_mapping.json ───────────────────────────────────────────────
nak_docs = chunk_nakshatras(DATA_DIR / "nakshatra_mapping.json")
check("nakshatra_mapping: produces docs", len(nak_docs) > 0, f"got {len(nak_docs)}")
check(
    "nakshatra_mapping: metadata has 'nakshatra'",
    "nakshatra" in nak_docs[0]["metadata"],
)

# ── houses.json ──────────────────────────────────────────────────────────
house_docs = chunk_houses(DATA_DIR / "houses.json")
check("houses: produces docs", len(house_docs) > 0, f"got {len(house_docs)}")
check("houses: 12 houses expected", len(house_docs) == 12, f"got {len(house_docs)}")
check(
    "houses: metadata has 'house_number'", "house_number" in house_docs[0]["metadata"]
)

# ── conjunctions.json ────────────────────────────────────────────────────
conj_docs = chunk_conjunctions(DATA_DIR / "conjunctions.json")
check("conjunctions: produces docs", len(conj_docs) > 0, f"got {len(conj_docs)}")
check("conjunctions: metadata has 'planets'", "planets" in conj_docs[0]["metadata"])

# ── numerology.json ──────────────────────────────────────────────────────
num_docs = chunk_numerology(DATA_DIR / "numerology.json")
check("numerology: produces docs", len(num_docs) > 0, f"got {len(num_docs)}")
check("numerology: metadata has 'number'", "number" in num_docs[0]["metadata"])

# ── guidance TXT files ───────────────────────────────────────────────────
for txt_file, domain in [
    ("career_guidance.txt", "career"),
    ("love_guidance.txt", "love"),
    ("spiritual_guidance.txt", "spiritual"),
]:
    path = DATA_DIR / txt_file
    if path.exists():
        g_docs = chunk_guidance_txt(path, domain)
        check(f"{txt_file}: produces docs", len(g_docs) > 0, f"got {len(g_docs)}")
        check(
            f"{txt_file}: metadata has 'domain'",
            g_docs[0]["metadata"].get("domain") == domain,
        )
    else:
        print(f"  {WARN}  {txt_file}: file not found — skipped")

# ── ID uniqueness across all docs ────────────────────────────────────────
all_local_docs = (
    zodiac_docs + planet_docs + nak_docs + house_docs + conj_docs + num_docs
)
all_ids = [d["id"] for d in all_local_docs]
unique_ids = set(all_ids)
check(
    f"Global ID uniqueness ({len(all_ids)} docs)",
    len(all_ids) == len(unique_ids),
    f"duplicates: {len(all_ids) - len(unique_ids)}",
)

total_chunks = len(all_local_docs)
print(f"\n  Total chunks from JSON files: {BOLD}{total_chunks}{RESET}")


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 2 — Indexing into ChromaDB (calls Gemini embedding API)
# ═══════════════════════════════════════════════════════════════════════════

section("PHASE 2 · Indexing (builds ChromaDB with text-embedding-004)")

from src.core.retrieval import init_store

try:
    count = init_store(str(DATA_DIR), force=True)
    check("Indexing completed", True)
    check(f"Documents indexed: {count}", count > 0, f"got {count}")
except Exception as exc:
    check("Indexing completed", False, str(exc))
    print(f"\n{FAIL}  Cannot proceed to search tests without a working index.")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 3 — Semantic Search
# ═══════════════════════════════════════════════════════════════════════════

section("PHASE 3 · Semantic Search")

from src.core.retrieval import search

# ── 3a. Unfiltered queries ───────────────────────────────────────────────
test_queries = [
    ("career strengths of Aries", None),
    ("Moon impact on love life", None),
    ("spiritual meaning of number 7", None),
    ("what does the 10th house represent", None),
    ("Sun and Jupiter conjunction career", None),
]

for query, filters in test_queries:
    results = search(query, filters=filters, n_results=3)
    ok = (
        len(results) > 0
        and results[0] != "Knowledge base is empty — please run indexing first."
    )
    check(f'Query: "{query}" → {len(results)} results', ok)
    if ok:
        preview = results[0][:120].replace("\n", " ")
        print(f"        ↳ top: {preview}…")

# ── 3b. Filtered queries ────────────────────────────────────────────────
filtered_queries = [
    ("personality traits", {"zodiac": "Scorpio"}, "zodiac filter"),
    ("career guidance", {"domain": "career"}, "domain filter"),
    ("planetary influence", {"planet": "Saturn"}, "planet filter"),
    ("house meaning", {"house_number": 7}, "house_number filter"),
    ("life path meaning", {"number": 3}, "number filter"),
]

for query, filters, label in filtered_queries:
    results = search(query, filters=filters, n_results=3)
    ok = len(results) > 0 and "No relevant passages" not in results[0]
    check(f'Filtered [{label}]: "{query}" → {len(results)} results', ok)
    if ok:
        preview = results[0][:120].replace("\n", " ")
        print(f"        ↳ top: {preview}…")


# ═══════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════

section("RESULTS")

if failures:
    print(f"\n  {FAIL}  {len(failures)} failure(s):\n")
    for f in failures:
        print(f"     • {f}")
    sys.exit(1)
else:
    print(f"\n  {PASS}  All checks passed!")
    sys.exit(0)
