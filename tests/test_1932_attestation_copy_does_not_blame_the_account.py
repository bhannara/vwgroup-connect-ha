# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""#1932/#1933 — the attestation notice asserted a diagnosis the code never made.

The tail read: the EU Data Act portal "did not work for **this account**
either: check in the portal that data sharing is enabled for your car."

Nothing establishes that. At that point the code knows only that the fallback
returned no data; it cannot see whether the portal refused this account or was
simply unreachable. On 2026-10-22 VW let the portal's TLS certificate expire,
and this sentence sent @RaAdNe and @mathiasolofsson87 through consent settings
that were already correct. @RaAdNe filed the wording itself as the bug.

It now states what is known — the fallback delivered nothing — and gives the
one check that separates the two causes: does the portal load in a browser.

**What these tests do not do.** They cannot judge a translation. Ten of the
twelve locales are the maintainer's own work and no native speaker has read
them; the mirror check below only proves a locale was not left carrying the
English source. A wrong-but-fluent translation would pass here.
"""
from __future__ import annotations

import json
import pathlib

import pytest

_PKG = pathlib.Path(__file__).resolve().parents[1] / "custom_components/vag_connect"
_SOURCE = _PKG / "strings.json"
_LOCALES = sorted((_PKG / "translations").glob("*.json"))

# the claim that had to go, verbatim
_BLAME = "did not work for this account"
# the check that replaced it
_THE_CHECK = "Open the portal in a browser"
_NOT_YOUR_FAULT = "nothing on your side needs changing"

_SPOTS = (
    ("config", "error", "eu_signin_attestation"),
    ("issues", "eu_signin_attestation", "description"),
)


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _at(obj: dict, spot: tuple[str, ...]) -> object:
    node: object = obj
    for key in spot:
        assert isinstance(node, dict), f"{'/'.join(spot)} is not reachable"
        node = node.get(key)
    return node


# ── the English source, which is the one text these tests can judge ────────


@pytest.mark.parametrize("spot", _SPOTS, ids=["config-error", "repair-description"])
def test_the_english_source_no_longer_blames_the_account(spot) -> None:
    text = _at(_load(_SOURCE), spot)
    assert isinstance(text, str) and text
    assert _BLAME not in text, (
        "the notice again asserts the portal refused THIS ACCOUNT, which the "
        "code cannot know — during a VW outage it is simply false"
    )


@pytest.mark.parametrize("spot", _SPOTS, ids=["config-error", "repair-description"])
def test_the_english_source_gives_the_check_that_separates_the_causes(spot) -> None:
    """Removing the false claim is only half of it. Without the browser check
    the user is left with "it didn't work" and no way forward."""
    text = _at(_load(_SOURCE), spot)
    assert isinstance(text, str)
    assert _THE_CHECK in text
    assert _NOT_YOUR_FAULT in text


def test_the_setup_error_text_matches() -> None:
    """``__init__.py`` carries its own shorter copy for the setup path, which is
    the text both reporters actually saw. It is a separate literal from
    strings.json, so it is asserted separately rather than assumed to follow."""
    from custom_components.vag_connect import _SETUP_ERRORS  # noqa: PLC0415

    text = _SETUP_ERRORS["eu_signin_attestation"]
    assert _BLAME not in text, f"the setup text blames the account: {text!r}"
    assert _THE_CHECK in text
    assert _NOT_YOUR_FAULT in text


# ── the mirror rule CONTRIBUTING.md states ─────────────────────────────────


def test_every_locale_is_present() -> None:
    """CONTRIBUTING.md: strings.json is the English source of truth and every
    change is mirrored into all 12 language files. Pinned so a dropped locale
    is a failure rather than a silently English repair card."""
    assert len(_LOCALES) == 12, [p.name for p in _LOCALES]


@pytest.mark.parametrize("path", _LOCALES, ids=lambda p: p.stem)
@pytest.mark.parametrize("spot", _SPOTS, ids=["config-error", "repair-description"])
def test_no_locale_was_left_carrying_the_old_claim(path, spot) -> None:
    text = _at(_load(path), spot)
    assert isinstance(text, str) and text, f"{path.name}: {'/'.join(spot)} missing"
    assert _BLAME not in text, (
        f"{path.name} still carries the English claim this change removed — "
        "either it was not mirrored, or it was reset to the source text"
    )


def test_the_english_locale_mirrors_the_source_exactly() -> None:
    """en.json is not a translation; a divergence there is a mistake."""
    src, en = _load(_SOURCE), _load(_PKG / "translations/en.json")
    for spot in _SPOTS:
        assert _at(src, spot) == _at(en, spot), f"en.json diverges at {'/'.join(spot)}"


@pytest.mark.parametrize("path", _LOCALES, ids=lambda p: p.stem)
def test_both_spots_say_the_same_thing_in_every_locale(path) -> None:
    """The two texts are the same sentence shown in two places (config error and
    repair card). They were identical in all 13 files before this change and
    must not drift apart now — a user who sees both would get two answers."""
    obj = _load(path)
    assert _at(obj, _SPOTS[0]) == _at(obj, _SPOTS[1]), (
        f"{path.name}: the config error and the repair description disagree"
    )
