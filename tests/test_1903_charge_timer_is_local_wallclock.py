# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""A charge timer two hours late, because the feed's ``Z`` is a lie.

@keylogicjohan (#1903) runs an ID.7 in Sweden (UTC+2). His EU Data Act feed
reported ``next_charge_timer_start_at = 2026-10-20T18:28:00Z`` for a session
his charger itself logged as starting ``2026-10-20T18:28:00+02:00``. So the
wall-clock reading is right and the ``Z`` is wrong: taken at face value the
sensors and the charging calendar ran two hours late.

His report is also the reason this is fixable narrowly rather than globally.
He cross-checked the OTHER timestamps in the same feed — ``last_seen_at``
against ``instrument_cluster_time`` — and they agree, so the feed is not
uniformly offset. This is two specific fields that are naive local time
wearing a UTC suffix, and the thirteen other callers of ``_epoch_or_iso`` in
that module are untouched.

**Naive is not an option as the output**, which is the part that decides the
shape of the fix. Every timestamp consumer here reads a naive value as UTC —
``raw.replace(tzinfo=timezone.utc)`` in the sensor layer,
``dt.replace(tzinfo=dt_util.UTC)`` in the calendar — so merely stripping the
suffix would re-create the same two-hour error one layer down, silently. The
reading is therefore re-stamped with the local zone.

Nothing here asserts a particular offset. The first version of these tests
did, and it passed only because this machine happens to run the same zone as
the reporter's car; in CI, which runs UTC, it would have failed. What is
asserted instead is the property that holds in every zone: the wall-clock
digits survive, and the result is timezone-aware.
"""
from __future__ import annotations

from datetime import datetime, timezone

from custom_components.vag_connect.cariad.auth._eu_data_act import (
    _epoch_or_iso,
    _local_wallclock,
)

#: His value, verbatim from the report.
HIS = "2026-10-20T18:28:00Z"
#: What his charger logged for the same session.
TRUTH = "2026-10-20T18:28:00+02:00"


def _local_offset() -> object:
    """Whatever zone this machine is in — the test must not care which."""
    return datetime.now().astimezone().utcoffset()


# ── the reported value ─────────────────────────────────────────────────────


def test_the_wallclock_reading_survives() -> None:
    """18:28 stays 18:28. That is the whole point: the digits were never
    wrong, only their claimed zone."""
    out = _local_wallclock(HIS)
    assert out is not None
    parsed = datetime.fromisoformat(out)
    assert (parsed.hour, parsed.minute) == (18, 28)
    assert parsed.date().isoformat() == "2026-10-20"


def test_the_result_is_timezone_aware() -> None:
    """Naive output would be re-read as UTC by every consumer, which is the
    bug. Pinned separately because it is the trap, not a detail."""
    parsed = datetime.fromisoformat(_local_wallclock(HIS) or "")
    assert parsed.tzinfo is not None, (
        "a naive value is interpreted as UTC downstream, so this would still "
        "be wrong by the local offset"
    )
    assert parsed.utcoffset() == _local_offset()


def test_it_is_no_longer_read_as_utc() -> None:
    """The regression, stated as the comparison that failed for him.

    The old behaviour kept the ``Z``, so the instant was 18:28 UTC. The new
    one is 18:28 local. In a zone with no offset those coincide and this test
    is vacuous — so it is skipped there rather than passing for free.
    """
    if _local_offset() == timezone.utc.utcoffset(None):
        import pytest

        pytest.skip("machine runs UTC; the two readings coincide here")
    old = datetime.fromisoformat(HIS.replace("Z", "+00:00"))
    new = datetime.fromisoformat(_local_wallclock(HIS) or "")
    assert new != old, "the value is still being taken as UTC"
    assert new.hour == old.hour, "the wall-clock reading must not shift"


def test_a_reporter_in_his_zone_gets_what_his_charger_logged() -> None:
    """End to end against his own cross-check, for the one zone where we can
    state the exact expected string: his."""
    if _local_offset() != datetime.fromisoformat(TRUTH).utcoffset():
        import pytest

        pytest.skip("this machine is not in the reporter's zone")
    assert _local_wallclock(HIS) == TRUTH


# ── the other shapes the helper has to accept ──────────────────────────────


def test_an_epoch_is_absolute_and_left_alone() -> None:
    """An epoch second needs none of this: it names an instant, not a
    wall-clock. It is handed to the original helper unchanged."""
    assert _local_wallclock("1761000480") == _epoch_or_iso("1761000480")


def test_an_already_naive_value_is_localised_too() -> None:
    parsed = datetime.fromisoformat(_local_wallclock("2026-10-20T18:28:00") or "")
    assert (parsed.hour, parsed.minute) == (18, 28)
    assert parsed.tzinfo is not None


def test_unparseable_input_passes_through() -> None:
    """Same contract as ``_epoch_or_iso``: do not invent a timestamp."""
    assert _local_wallclock("not-a-time") == "not-a-time"
    assert _local_wallclock(None) is None
    assert _local_wallclock("") is None


# ── and the thirteen other callers keep their meaning ──────────────────────


def test_the_other_fields_still_read_their_z_as_utc() -> None:
    """The narrowing is the fix's safety. ``last_seen_at`` and the rest are
    genuinely UTC — he verified that himself — so ``_epoch_or_iso`` must be
    unchanged for them."""
    assert _epoch_or_iso("2026-10-20T19:36:11Z") == "2026-10-20T19:36:11Z"


def test_only_the_two_timer_fields_use_the_new_helper() -> None:
    """Guards the scope. If a third field starts calling it, that is a
    decision someone should have to make on purpose."""
    import inspect
    import re

    from custom_components.vag_connect.cariad.auth import _eu_data_act as eda

    src = inspect.getsource(eda)
    # the helper's own definition and docstring mention it; count assignments
    callers = re.findall(r"d\.(\w+)\s*=\s*_local_wallclock\(", src)
    assert sorted(callers) == [
        "next_charge_timer_finish_at",
        "next_charge_timer_start_at",
    ], f"unexpected callers: {sorted(callers)}"
