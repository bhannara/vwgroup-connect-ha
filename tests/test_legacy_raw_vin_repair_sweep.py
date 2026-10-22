# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""A changelog promised a cleanup that the code never performed.

A repair's ``issue_id`` lands verbatim in Home Assistant's own config-entry
diagnostics, which this integration's VIN redaction never sees — the code says
so itself in ``repairs.py``. #1768 stopped new ``historical_timeout`` cards
being created with a raw VIN, and the v4.12.0 changelog told users that "any
card created before this update is cleared on upgrade so nothing lingers".

**It did not clear them.** The legacy delete lives inside
``raise_issue_historical_timeout`` and ``clear_issue_historical_timeout``, so
it only runs when that same repair is next raised or cleared:

* the raise path builds its work list from ``state == "pending"`` only and
  returns early when that list is empty, so a VIN parked in ``timed_out`` is
  never in it;
* the clear path has exactly one caller — a manual user off-switch.

So for the state the card exists *in*, neither ever fires. A card raised before
the upgrade survives it indefinitely.

**Measured, not inferred.** A user running v5.1.1 — two releases past the fix —
attached a diagnostics file to a public issue that still carried the full
17-character VIN in that id.

Scoped to ``historical_timeout`` deliberately. The ``stale_data`` sibling
(#1626) has the same id shape and *not* the same gap: its clear runs inside
``_enrich`` on every poll, so its legacy id goes on the first poll after an
upgrade. A sweep for it would be dead code, and this file asserts that
distinction rather than leaving it to memory.
"""
from __future__ import annotations

import ast
import inspect
import pathlib
from unittest.mock import MagicMock, patch

import pytest

from custom_components.vag_connect import repairs
from custom_components.vag_connect.const import DOMAIN

_VIN = "WVWZZZAUZFW000000"


# ── the sweep itself ───────────────────────────────────────────────────────


def test_it_deletes_the_raw_vin_id() -> None:
    """The reported case: a card whose id carries the whole VIN."""
    hass = MagicMock()
    with patch.object(repairs.ir, "async_delete_issue") as deleted:
        repairs.sweep_legacy_raw_vin_issues(hass, "entry1", [_VIN])
    deleted.assert_called_once_with(
        hass, DOMAIN, f"entry1_historical_timeout_{_VIN}"
    )


def test_it_sweeps_every_known_vin() -> None:
    """A two-car account has two cards, and sweeping one is not a fix."""
    hass = MagicMock()
    second = "WVWZZZAUZFW111111"
    with patch.object(repairs.ir, "async_delete_issue") as deleted:
        repairs.sweep_legacy_raw_vin_issues(hass, "entry1", [_VIN, second])
    ids = {call.args[2] for call in deleted.call_args_list}
    assert ids == {
        f"entry1_historical_timeout_{_VIN}",
        f"entry1_historical_timeout_{second}",
    }


@pytest.mark.parametrize("junk", [None, "", 0, [], {}])
def test_rubbish_in_the_vin_list_is_skipped(junk: object) -> None:
    """The list comes from a restored snapshot, which is user data that has
    been through a disk round-trip. A bad entry must not raise here."""
    hass = MagicMock()
    with patch.object(repairs.ir, "async_delete_issue") as deleted:
        repairs.sweep_legacy_raw_vin_issues(hass, "entry1", [junk, _VIN])
    assert deleted.call_count == 1


def test_it_does_not_touch_the_masked_id() -> None:
    """The masked card is the *current* one and may legitimately be showing.
    Deleting it would silence a live warning while tidying an old id."""
    hass = MagicMock()
    with patch.object(repairs.ir, "async_delete_issue") as deleted:
        repairs.sweep_legacy_raw_vin_issues(hass, "entry1", [_VIN])
    for call in deleted.call_args_list:
        assert repairs.mask_vin(_VIN) not in call.args[2], (
            f"the sweep deleted the current masked card: {call.args[2]}"
        )


def test_an_empty_list_does_nothing() -> None:
    hass = MagicMock()
    with patch.object(repairs.ir, "async_delete_issue") as deleted:
        repairs.sweep_legacy_raw_vin_issues(hass, "entry1", [])
    deleted.assert_not_called()


# ── it has to actually run ─────────────────────────────────────────────────


def test_setup_calls_the_sweep() -> None:
    """A sweep nothing invokes is the same bug with more code in it."""
    import custom_components.vag_connect.coordinator as coord_mod

    source = pathlib.Path(coord_mod.__file__).read_text(encoding="utf-8")
    assert "sweep_legacy_raw_vin_issues(" in source, (
        "nothing calls the sweep, so a legacy raw-VIN card still survives an "
        "upgrade"
    )
    tree = ast.parse(source)
    callers = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and "sweep_legacy_raw_vin_issues(" in (ast.get_source_segment(source, node) or "")
    ]
    assert "async_setup" in callers, (
        f"the sweep is not called from setup, so it no longer runs once per "
        f"start: {callers}"
    )


def test_a_failing_sweep_does_not_stop_setup() -> None:
    """Tidying old cards must never be why an entry fails to load. The leak is
    bad; an integration that will not start is worse, and the card stays
    deletable by hand either way."""
    import custom_components.vag_connect.coordinator as coord_mod

    source = pathlib.Path(coord_mod.__file__).read_text(encoding="utf-8")
    idx = source.index("sweep_legacy_raw_vin_issues(\n")
    window = source[max(0, idx - 700):idx + 400]
    assert "try:" in window and "except Exception" in window, (
        "the sweep is no longer guarded; a registry error during cleanup would "
        "now take the whole entry down"
    )


# ── the scope decision, pinned rather than remembered ──────────────────────


def test_the_stale_data_sibling_is_not_swept() -> None:
    """It does not need it, and a sweep for it would be dead code.

    ``clear_stale_data_issue`` runs from ``_enrich`` on every poll, so the
    legacy id goes on the first poll after an upgrade. This is asserted rather
    than left in a comment, because the two repairs look identical and the
    obvious instinct is to treat them the same.
    """
    src = inspect.getsource(repairs.sweep_legacy_raw_vin_issues)
    assert "stale_data" not in src.split('"""')[-1], (
        "the sweep now touches stale_data too; check whether it actually needs "
        "it before widening — it self-heals on the next poll"
    )

    import custom_components.vag_connect.coordinator as coord_mod

    enrich = inspect.getsource(coord_mod.VagConnectCoordinator._enrich)
    assert "clear_stale_data_issue(" in enrich, (
        "stale_data's clear left the per-poll path, so it no longer self-heals "
        "and the scope decision above needs revisiting"
    )


def test_the_raw_vin_never_reaches_a_current_card() -> None:
    """The #1768 half, still holding. The sweep cleans history; this is what
    stops history being made again."""
    for fn in (
        repairs.raise_issue_historical_timeout,
        repairs.clear_issue_historical_timeout,
    ):
        src = inspect.getsource(fn)
        created = [
            line
            for line in src.splitlines()
            if "async_create_issue" in line or "f\"{entry_id}_historical_timeout_" in line
        ]
        assert any("mask_vin(vin)" in line for line in created), (
            f"{fn.__name__} no longer masks the VIN in the id it creates"
        )
