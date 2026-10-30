# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""#1950 (@Adcad1970, Audi A6 e-tron) — the lock sensors now carry the car's own
capture time, not just "dataset".

He asked when the closure and lock sensors had last been captured, and the first
answer he got was wrong twice over. The parser was never the problem: on 30
October he sent the shape of two real deliveries, and every one of his six lock
entries carries its own ``timestampUtc``. His own reading of it was right — "if
the mapper currently drops timestampUtc on this shape, that's where the lock
stamps are." It does not drop them; they were being lost one step later, at
attribution, because recording a stamp is opt-in per mapper call site and no
lock or closure site asked for it.

His delivery is also the counter-example to the shape this code was written
around: a flat list of {key, dataFieldName, value, timestampUtc} objects with no
``car_captured_*`` marker anywhere, and an entry ORDER that changed between two
files generated 44 minutes apart (his lock positions moved from 3/11/17/29/36/40
to 62/9/65/47/54/14). Nothing here may depend on position.

THE AGGREGATE POLICY, written down because it is a decision and not a discovery:
``doors_locked`` is ``all(doors locked)`` over up to four per-door leaves, so the
verdict is only as trustworthy as its STALEST member. The recorded stamp is
therefore the OLDEST reporting door's, and when any reporting door carries no
stamp at all the verdict stays unstamped rather than borrowing a sibling's time.
The tailgate and the bonnet are single fields and need no policy.
"""
from __future__ import annotations

from custom_components.vag_connect.cariad.auth._eu_data_act import (
    _walk_fields,
    map_dataset_to_vehicle_data,
)
from custom_components.vag_connect.cariad.models import VehicleData

_BULK = "2026-10-28T21:05:00Z"
_OLDER = "2026-10-27T21:05:00Z"

# His order, from the 09:21 file, deliberately NOT the order the mapper lists.
_LOCKS = (
    "locked_state_rear_right_door",
    "locked_state_front_left_door",
    "locked_state__rear_left_door",  # double underscore, as delivered
    "locked_state_tailgate",
    "locked_state_front_engine_bonnet",
    "locked_state_front_right_door",
)


def _delivery(
    *, locked: bool = True, stamps: dict[str, str] | None = None,
    unstamped: tuple[str, ...] = (),
) -> dict[str, object]:
    """His shape: a flat list, every entry its own stamp, no capture marker."""
    stamps = stamps or {}
    data: list[dict[str, object]] = []
    for i, name in enumerate(_LOCKS):
        entry: dict[str, object] = {
            "key": f"k{i}",
            "dataFieldName": name,
            "value": 2 if locked else 3,
        }
        if name not in unstamped:
            entry["timestampUtc"] = stamps.get(name, _BULK)
        data.append(entry)
    return {"vin": "X", "Data": data}


def _mapped(payload: dict[str, object]) -> VehicleData:
    ts: dict[str, float] = {}
    fields = _walk_fields(payload, _ts_out=ts)
    return map_dataset_to_vehicle_data(fields, VehicleData(vin="X"), field_ts=ts)


# --- the stamps arrive ------------------------------------------------------

def test_all_three_lock_verdicts_carry_a_capture_time() -> None:
    d = _mapped(_delivery())
    assert (d.doors_locked, d.trunk_locked, d.bonnet_locked) == (True, True, True)
    for attr in ("doors_locked", "trunk_locked", "bonnet_locked"):
        assert d.field_captured_ts.get(attr), f"{attr} carries no capture time"


def test_the_single_field_verdicts_use_their_own_leaf() -> None:
    d = _mapped(_delivery())
    assert d.field_source_leaf.get("trunk_locked") == "locked_state_tailgate"
    assert (
        d.field_source_leaf.get("bonnet_locked")
        == "locked_state_front_engine_bonnet"
    )


# --- the aggregate policy ---------------------------------------------------

def test_the_door_verdict_takes_the_oldest_reporting_door() -> None:
    """The stalest member bounds the verdict. Pinned because the freshest member
    is the tempting choice and would advertise confidence the verdict lacks."""
    d = _mapped(
        _delivery(stamps={"locked_state__rear_left_door": _OLDER})
    )
    assert d.field_source_leaf.get("doors_locked") == "locked_state__rear_left_door"
    assert d.field_captured_ts["doors_locked"].startswith("2026-10-27")


def test_a_door_without_a_stamp_leaves_the_verdict_unstamped() -> None:
    """Borrowing a sibling's time would make the aggregate look newer than the
    evidence. No stamp is the honest outcome, and the sensor then says
    "dataset" as before — not a wrong "point"."""
    d = _mapped(_delivery(unstamped=("locked_state_front_right_door",)))
    assert d.doors_locked is True, "the verdict itself must be unaffected"
    assert "doors_locked" not in d.field_captured_ts
    # the single-field verdicts beside it are untouched
    assert d.field_captured_ts.get("trunk_locked")


def test_the_tailgate_does_not_stamp_the_door_verdict() -> None:
    """#1950's first half was that the tailgate is not a door. It must not
    become a door again by way of the capture stamp."""
    d = _mapped(_delivery(stamps={"locked_state_tailgate": _OLDER}))
    assert d.field_source_leaf.get("doors_locked") != "locked_state_tailgate"
    assert d.field_captured_ts["doors_locked"].startswith("2026-10-28")


def test_order_in_the_delivery_does_not_decide_the_stamp() -> None:
    """His two files delivered the same six locks in different positions, so a
    result that moves with the order would be wrong on at least one of them."""
    stamps = {"locked_state_rear_right_door": _OLDER}
    first = _mapped(_delivery(stamps=stamps))
    shuffled = _delivery(stamps=stamps)
    shuffled["Data"] = list(reversed(shuffled["Data"]))  # type: ignore[index]
    second = _mapped(shuffled)
    assert (
        first.field_source_leaf.get("doors_locked")
        == second.field_source_leaf.get("doors_locked")
        == "locked_state_rear_right_door"
    )
    assert (
        first.field_captured_ts["doors_locked"]
        == second.field_captured_ts["doors_locked"]
    )


# --- the stamp belongs to the value it is attached to -----------------------

def test_an_invalid_lock_reading_records_nothing() -> None:
    """0=unsupported and 1=invalid are not readings. A stamp on one of those
    would be a capture time for a value the car never reported."""
    payload = _delivery()
    for entry in payload["Data"]:  # type: ignore[attr-defined]
        if entry["dataFieldName"] == "locked_state_front_engine_bonnet":
            entry["value"] = 1
    d = _mapped(payload)
    assert d.bonnet_locked is None
    assert "bonnet_locked" not in d.field_captured_ts
    assert "bonnet_locked" not in d.field_source_leaf


def test_an_unlocked_door_still_stamps_the_verdict() -> None:
    """The stamp is about WHEN, not about what the verdict is."""
    d = _mapped(_delivery(locked=False))
    assert d.doors_locked is False
    assert d.field_captured_ts.get("doors_locked")
