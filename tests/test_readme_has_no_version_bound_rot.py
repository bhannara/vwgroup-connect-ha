"""The READMEs may not restate facts that have a source of truth elsewhere.

Why this is a test and not a convention: the English README claimed
``Minimum Home Assistant: 2024.4.0`` while ``hacs.json`` required ``2026.6.0``.
Two and a half years of drift, in the one line a prospective user reads before
installing — and HACS then refuses the install with a number that contradicts the
documentation. Nothing caught it, because nothing was looking.

Three classes of claim are forbidden here, each for the same reason:

1. **Minimum Home Assistant version**, typed by hand. It lives in ``hacs.json``,
   which is what HACS enforces. The badge reads that file live, so it cannot
   drift; a second hand-typed copy can and did.
2. **"new in X.Y.Z" markers.** That is the CHANGELOG's job. Once the current
   release is several majors past, such a marker tells a reader nothing and makes
   the document read like archaeology.
3. **Counted claims** such as "100+ entities" or "30+ service calls". Nobody
   recounts them, so they are decoration that ages; one even quoted the entity
   count of a single contributor's car.

Every pattern below is checked against a synthetic sample that it MUST match, so
a regex that silently stops matching cannot let the whole file pass as clean.
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_READMES = sorted(_ROOT.glob("README*.md"))

# "new in 4.3.0", "from 3.0.0", "since v2.29.0", "in 3.0.1 when"
_VERSION_MARKER = re.compile(
    r"\b(?:new in|from|since)\s+v?\d+\.\d+(?:\.\d+)?\b", re.IGNORECASE
)
# "100+ entities", "30+ service calls", "(58 entities)"
_COUNT_CLAIM = re.compile(
    r"\b\d{2,}\s*\+?\s*(?:entities|service calls)\b|\(\s*\d{2,}\s+entities\s*\)",
    re.IGNORECASE,
)
# A Home Assistant minimum typed as a literal calendar version.
_HARDCODED_MINIMUM = re.compile(
    r"(?:minimum|requires?|needs)[^\n]{0,40}?\b20\d\d\.\d+(?:\.\d+)?\b", re.IGNORECASE
)


def test_the_readmes_exist_at_all() -> None:
    """Guards every other test here: an empty glob passes everything."""
    assert len(_READMES) >= 2, (
        f"found {len(_READMES)} README files at the repo root; the globbing is "
        "broken and every check below would pass without reading anything"
    )
    assert (_ROOT / "README.md") in _READMES


def test_the_patterns_can_actually_fire() -> None:
    """Positive control for all three patterns, so none can pass vacuously."""
    assert _VERSION_MARKER.search("the dongle reader (new in 4.3.0) is read-only")
    assert _VERSION_MARKER.search("carries raw responses from 3.0.0 onwards")
    assert _VERSION_MARKER.search("the request has no expiry since v2.29.0")
    assert _COUNT_CLAIM.search("100+ entities across multiple platforms")
    assert _COUNT_CLAIM.search("ships 30+ service calls")
    assert _COUNT_CLAIM.search("confirmed on a live US Audi Q5 (58 entities)")
    assert _HARDCODED_MINIMUM.search("Minimum Home Assistant: `2024.4.0`.")
    assert _HARDCODED_MINIMUM.search("requires Home Assistant 2026.6.0 or newer")
    # Negative controls: these must NOT fire, or the guard is unusable.
    assert not _VERSION_MARKER.search("read from hacs.json, so it cannot drift")
    assert not _COUNT_CLAIM.search("entity names in 12 languages")
    assert not _HARDCODED_MINIMUM.search("the badge at the top of this page")


@pytest.mark.parametrize("path", _READMES, ids=lambda p: p.name)
def test_no_version_marker(path: pathlib.Path) -> None:
    hits = [
        f"line {n}: {m.group(0)}"
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if not line.lstrip().startswith("<!--")
        for m in [_VERSION_MARKER.search(line)]
        if m
    ]
    assert not hits, (
        f"{path.name} dates a feature to a release. That belongs in the "
        f"CHANGELOG; here it only ages: {hits}"
    )


@pytest.mark.parametrize("path", _READMES, ids=lambda p: p.name)
def test_no_counted_claim(path: pathlib.Path) -> None:
    hits = [
        f"line {n}: {m.group(0)}"
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        for m in [_COUNT_CLAIM.search(line)]
        if m
    ]
    assert not hits, (
        f"{path.name} counts something nobody will recount: {hits}. Describe the "
        "capability instead, or enumerate it so the list is its own source."
    )


@pytest.mark.parametrize("path", _READMES, ids=lambda p: p.name)
def test_no_hardcoded_minimum_version(path: pathlib.Path) -> None:
    hits = [
        f"line {n}: {line.strip()[:90]}"
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if _HARDCODED_MINIMUM.search(line)
    ]
    assert not hits, (
        f"{path.name} states a minimum Home Assistant version by hand. It lives "
        f"in hacs.json and the badge reads that file live: {hits}"
    )


_TRANSLATIONS = [p for p in _READMES if p.name != "README.md"]

# Any calendar version written with a dot: 2024.4, 2026.6.0. Deliberately does
# NOT match a date like 2026-08-13, which is a legitimate historical fact.
_CALENDAR_VERSION = re.compile(r"\b20\d\d\.\d+(?:\.\d+)?\b")


def test_the_translation_set_is_not_empty() -> None:
    """Guards the two tests below; an empty list would pass them silently."""
    assert len(_TRANSLATIONS) >= 5, (
        f"only {len(_TRANSLATIONS)} translated READMEs found, so the checks "
        "below would pass without reading anything"
    )


def test_the_calendar_version_pattern_can_fire() -> None:
    assert _CALENDAR_VERSION.search("Minimum Home Assistant: 2024.4.0")
    assert _CALENDAR_VERSION.search("needs HA Core 2026.7 or newer")
    # A date must not be mistaken for a version, or the ban is unusable.
    assert not _CALENDAR_VERSION.search("VW closed this on 2026-08-13")


@pytest.mark.parametrize("path", _TRANSLATIONS, ids=lambda p: p.name)
def test_a_translation_names_no_version_at_all(path: pathlib.Path) -> None:
    """The strict form of the ban, and the reason it can be strict here.

    ``test_no_hardcoded_minimum_version`` keys off English words like
    "minimum", so it only ever caught the translations whose phrasing stayed
    close to English — measured: four of eleven, while the stale version sat in
    all of them. A keyword list cannot be completed across eleven languages.

    These pages are deliberately short summaries that point at the English one,
    so they have no legitimate reason to carry a version number of any kind.
    That makes a blanket ban possible, and a blanket ban is language-independent.
    """
    hits = [
        f"line {n}: {line.strip()[:90]}"
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if _CALENDAR_VERSION.search(line)
    ]
    assert not hits, (
        f"{path.name} names a version. A translated summary must not: it will "
        f"not be updated when the number changes, and that is exactly how these "
        f"pages went two years out of date: {hits}"
    )


@pytest.mark.parametrize("path", _TRANSLATIONS, ids=lambda p: p.name)
def test_a_translation_stays_a_summary_and_points_at_the_canonical_page(
    path: pathlib.Path,
) -> None:
    """Keeps the decision from being undone by a well-meaning expansion.

    These were full copies once. Each edit to the English page silently
    invalidated eleven files, and they ended up seven weeks behind. Short pages
    that defer to one authoritative page are maintainable; twelve full documents
    are not. If someone grows one back into a full translation, this fails and
    says why.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert "README.md" in text, (
        f"{path.name} does not link to the English README, so a reader has no "
        "route to the authoritative page"
    )
    assert "shields.io/badge/dynamic/json" in text, (
        f"{path.name} lost the derived Home Assistant badge; without it the page "
        "either states no requirement or will state a stale one"
    )
    assert len(lines) <= 120, (
        f"{path.name} has grown to {len(lines)} lines. These pages are summaries "
        "on purpose — a full translation falls behind the English page within "
        "weeks, which is the state this replaced."
    )


def test_the_badge_reads_the_requirement_from_hacs_json() -> None:
    """The replacement for the hand-typed minimum has to actually be wired up.

    Removing the stale line is only half the fix. If the badge were also static,
    the next reader would get a different wrong number instead of the same one.
    """
    text = (_ROOT / "README.md").read_text(encoding="utf-8")
    assert "shields.io/badge/dynamic/json" in text, (
        "the Home Assistant badge is not derived; a static badge is the same "
        "defect as the line that was removed"
    )
    assert "hacs.json" in text and "%24.homeassistant" in text, (
        "the dynamic badge does not query hacs.json's homeassistant key"
    )
    # And the source it reads must exist with that key, or the badge renders an
    # error in the one place every visitor looks.
    hacs = json.loads((_ROOT / "hacs.json").read_text(encoding="utf-8"))
    assert "homeassistant" in hacs, (
        "hacs.json has no 'homeassistant' key, so the badge the README relies on "
        "would render as an error"
    )
