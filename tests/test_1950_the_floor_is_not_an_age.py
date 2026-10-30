# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""#1950 — three comments called the dataset-level capture time a "~15-min
floor", and that wording reached a reporter as an answer.

The parser was always right; only the prose about it was wrong. Prose cannot be
regression-tested by reading it, so this module pins the properties the
corrected comments now assert, and guards the phrase itself.

Why it mattered beyond tidiness: @Adcad1970 asked when the closure and lock
sensors had last been captured, and the answer priced the floor at "roughly
fifteen minutes". It is not a duration at all. #1688 (@Datendieb) is the
standing counter-example in this repo: his export carried every data point at
16:59/17:00 while the car's own ``car_captured_*`` field sat five days earlier.
A floor read off that field is therefore neither an upper bound on age nor a
stand-in for the export's freshest reading.

The second thing pinned here was found by measuring rather than by reading. A
recorded capture time does NOT have to come from the leaf's own sibling key: a
``car_captured_*`` marker standing earlier in the SAME list becomes the capture
time of the items that follow it, which is the shape most exports use and is
correct — VW groups a block of points under one stamp. What never happens is the
payload-wide floor being handed to a field in another branch. Those two routes
look alike in a single-marker file and are easy to conflate in a comment, which
is how the original wording got away with being wrong for so long.
"""
from __future__ import annotations

import inspect
import re
from pathlib import Path

from custom_components.vag_connect.cariad.auth._eu_data_act import (
    _dataset_captured_ts,
    _parse_ts,
    _walk_fields,
)

# The #1688 shape: the car's own capture field frozen days behind the points.
_FROZEN_MARKER = "2026-09-28T09:49:00Z"
_FRESH_POINT = "2026-10-03T16:59:00Z"


# --- what the floor is, and what it is not ----------------------------------

def test_the_floor_can_be_older_than_a_genuine_point_stamp() -> None:
    """What the old comments implied — "as fresh as the export's freshest
    reading" — is false in the one shape this repo has a named case for."""
    payload = {
        "data": [
            {"dataFieldName": "car_captured_time", "value": _FROZEN_MARKER},
            {
                "dataFieldName": "battery_state_report.soc",
                "value": 82,
                "timestampUtc": _FRESH_POINT,
            },
        ]
    }
    floor = _dataset_captured_ts(payload)
    fresh = _parse_ts(_FRESH_POINT)
    assert floor is not None and fresh is not None
    assert floor < fresh, (
        "the floor is the newest CAR-CAPTURED stamp, not the export's freshest "
        "reading; if that ever stops holding, the comments in entity_base.py, "
        "cariad/models.py and cariad/auth/_eu_data_act.py need rewording"
    )


def test_the_floor_reports_vws_stamp_verbatim() -> None:
    """15 minutes is the portal's publish cadence, not an age. Nothing clamps
    the floor to it, so a frozen field stays exactly as old as VW sent it."""
    marker_only = {"meta": {"car_captured_time": _FROZEN_MARKER}}
    assert _dataset_captured_ts(marker_only) == _parse_ts(_FROZEN_MARKER)


def test_the_payload_wide_floor_never_reaches_the_per_point_map() -> None:
    """``field_captured_ts`` promises a genuine capture time, so the inherited
    floor must contribute no entry — otherwise a sensor would present a stamp
    belonging to some other branch of the file as its own measurement time."""
    ts: dict[str, float] = {}
    out = _walk_fields(
        {
            "meta": {"car_captured_time": _FROZEN_MARKER},
            "data": [{"dataFieldName": "doors.locked", "value": 2}],
        },
        _ts_out=ts,
    )
    assert out.get("doors.locked") == "2", "the bare value must still be parsed"
    assert "doors.locked" not in ts, (
        "a field in another branch received the payload-wide floor; it is "
        "leaking into the map that feeds data_captured_at"
    )


def test_a_marker_in_the_same_list_is_a_genuine_stamp_for_what_follows() -> None:
    """Deliberate, and the reason "per-point" is narrower in words than in
    fact: VW groups a block of points under one ``car_captured_*`` item, so the
    items after it are stamped from it. Pinned so it is not "fixed" away."""
    ts: dict[str, float] = {}
    _walk_fields(
        {
            "data": [
                {"dataFieldName": "car_captured_time", "value": _FROZEN_MARKER},
                {"dataFieldName": "doors.locked", "value": 2},
            ]
        },
        _ts_out=ts,
    )
    assert ts.get("doors.locked") == _parse_ts(_FROZEN_MARKER), (
        "an item following a capture marker in the same list lost its stamp"
    )


def test_a_leafs_own_timestamp_beats_the_list_marker() -> None:
    """Precedence, measured: the marker is a fallback for items that carry no
    timestamp of their own, never an override of one that does."""
    ts: dict[str, float] = {}
    _walk_fields(
        {
            "data": [
                {"dataFieldName": "car_captured_time", "value": _FROZEN_MARKER},
                {
                    "dataFieldName": "battery_state_report.soc",
                    "value": 82,
                    "timestampUtc": _FRESH_POINT,
                },
            ]
        },
        _ts_out=ts,
    )
    assert ts.get("battery_state_report.soc") == _parse_ts(_FRESH_POINT), (
        "the list marker overrode a point's own capture time"
    )


# --- the guard, so the wrong phrase cannot come back quietly ----------------

_WRONG = re.compile(
    r"15[^a-z]{0,2}min[a-z]*[^.\n]{0,60}(dataset|batch)[ -]?floor"
    r"|(dataset|batch)[ -]?floor[^.\n]{0,60}15[^a-z]{0,2}min"
    r"|15[^a-z]{0,2}min[a-z]*[ -]old",
    re.IGNORECASE,
)

_PACKAGE = Path(__file__).resolve().parents[1] / "custom_components" / "vag_connect"


def test_no_comment_prices_a_portal_value_at_fifteen_minutes() -> None:
    """A correction that lives only in a changelog guards nothing.

    15 minutes is a real number in this integration — the publish cadence, the
    poll floor, an e-mail-code interval — so this does NOT forbid mentioning it.
    It forbids attaching it to the dataset/batch FLOOR or to the AGE of a value,
    which is the specific claim #1950 was answered with.

    Note for whoever this fails on: the pattern cannot tell an assertion from a
    denial, so do not "answer" it by writing that a value is *not* 15 minutes
    old. Say what it is instead. That is why no comment in the package quotes
    the old phrasing, not even to disown it.
    """
    # Positive control first: an instrument that matches nothing proves nothing.
    assert _WRONG.search("else 'dataset' for the ~15-min batch floor")
    assert _WRONG.search("its 15-min-old pin would outrank a live fix")
    assert not _WRONG.search("the portal publishes a new drop every 15 minutes")
    assert not _WRONG.search("polling is throttled to 15 min")

    offenders = []
    for path in sorted(_PACKAGE.rglob("*.py")):
        for n, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if _WRONG.search(line):
                offenders.append(f"{path.name}:{n}: {line.strip()}")
    assert not offenders, (
        "a comment again prices a portal value at ~15 minutes:\n"
        + "\n".join(offenders)
    )


def test_the_freshness_attribute_docstring_says_the_narrow_thing() -> None:
    """``freshness_source: "dataset"`` is the else-branch of "no per-point stamp
    was recorded", not a statement that a floor was inherited. The docstring has
    to say the narrower thing, because the wider one is what misled #1950."""
    from custom_components.vag_connect.entity_base import VagConnectEntity

    doc = inspect.getdoc(VagConnectEntity._eu_da_freshness_attributes) or ""
    assert doc, "the method lost its docstring"
    assert "recorded" in doc.lower(), (
        "the docstring no longer says that 'dataset' only means no per-point "
        "stamp was RECORDED for this attribute"
    )
