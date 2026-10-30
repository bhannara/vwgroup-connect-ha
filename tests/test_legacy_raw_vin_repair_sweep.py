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

**#923 (@skornehl) — the scope was wrong, and this file used to pin the wrong
reason.** It asserted that sweeping the ``stale_data`` sibling (#1626) would be
dead code, because that card's clear runs inside ``_enrich`` on every poll and
so heals itself on the first poll after an upgrade. True — *while the car still
polls.* He runs two vehicles, one sold and disabled. Its card was raised on
2026-09-14 carrying the raw VIN, the vehicle never polls again, ``_enrich``
never runs for it, and two releases later the full VIN was still in that id. He
stripped it out by hand before attaching his diagnostics to a public issue.

Two further holes the same report exposed, both of them in the *shape* of the
fix rather than in its intent:

* the sweep took a list of VINs, and a sold car is in no list this code can
  build — it is not in ``self.vehicles`` at all;
* the call sat inside the cache-restore branch, so an entry with no cached
  snapshot never swept anything.

So the sweep now walks the integration's own issue registry and deletes any id
ending in something VIN-shaped, and it runs on every setup. The tests below pin
both, and the old scope assertion is inverted rather than deleted, so the
history of the decision stays readable.
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
    ids = {call.args[2] for call in deleted.call_args_list}
    assert f"entry1_historical_timeout_{_VIN}" in ids


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
        f"entry1_stale_data_{_VIN}",
        f"entry1_stale_data_{second}",
    }


@pytest.mark.parametrize("junk", [None, "", 0, [], {}])
def test_rubbish_in_the_vin_list_is_skipped(junk: object) -> None:
    """The list comes from a restored snapshot, which is user data that has
    been through a disk round-trip. A bad entry must not raise here."""
    hass = MagicMock()
    with patch.object(repairs.ir, "async_delete_issue") as deleted:
        repairs.sweep_legacy_raw_vin_issues(hass, "entry1", [junk, _VIN])
    # Two families per surviving VIN, and nothing at all for the junk entry.
    assert deleted.call_count == 2


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


def _registry(*issue_ids: str, domain: str = DOMAIN):
    """A stub issue registry shaped like Home Assistant's.

    ``IssueRegistry.issues`` is a ``dict[tuple[domain, issue_id], entry]``,
    verified against the installed homeassistant package rather than assumed.
    """
    stub = MagicMock()
    stub.issues = {(domain, iid): object() for iid in issue_ids}
    return stub


def _swept(registry, vins: list[str], entry_id: str = "entry1") -> set[str]:
    hass = MagicMock()
    with patch.object(repairs.ir, "async_get", return_value=registry), \
            patch.object(repairs.ir, "async_delete_issue") as deleted:
        repairs.sweep_legacy_raw_vin_issues(hass, entry_id, vins)
    return {call.args[2] for call in deleted.call_args_list}


def test_an_empty_vin_list_still_sweeps_the_registry() -> None:
    """#923 — the whole point of the rewrite.

    The VIN list is built from the vehicles that still exist. A sold or
    disabled car is in no such list, so a sweep that needs one can never reach
    its card. With an empty list there must still be a sweep.
    """
    gone = f"entry1_stale_data_{_VIN}"
    assert gone in _swept(_registry(gone), [])


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


def test_the_stale_data_sibling_is_swept_too() -> None:
    """#923 — this assertion is the inverse of the one it replaces.

    The old test pinned the scope decision: ``stale_data`` needs no sweep
    because ``clear_stale_data_issue`` runs from ``_enrich`` on every poll. The
    premise was never wrong, only incomplete — it describes a car that still
    polls. A sold, disabled vehicle never polls again, so its card never heals,
    and that is the card found in a public upload.
    """
    src = inspect.getsource(repairs.sweep_legacy_raw_vin_issues)
    assert "stale_data" in src, (
        "the sweep stopped covering stale_data; a card left by a vehicle that "
        "no longer polls will survive upgrades again (#923)"
    )
    assert f"entry1_stale_data_{_VIN}" in _swept(_registry(), [_VIN])


def test_a_card_from_a_vin_the_entry_never_heard_of_is_swept() -> None:
    """The reported case: the VIN belongs to a car sold months ago."""
    sold = "WVWZZZAUZFW222222"
    assert f"entry1_stale_data_{sold}" in _swept(
        _registry(f"entry1_stale_data_{sold}"), [_VIN]
    )


def test_a_card_left_by_a_removed_entry_is_swept() -> None:
    """Remove and re-add the integration and the old id keeps the old
    entry_id, so an entry-scoped sweep would never reach it. A raw VIN in one
    of our ids is a leak whichever entry wrote it."""
    orphan = f"someoldentry_stale_data_{_VIN}"
    assert orphan in _swept(_registry(orphan), [])


def test_the_masked_card_survives_the_registry_scan() -> None:
    """The masked card is the *current* one and may be showing a live warning.
    Deleting it would silence a real problem while tidying an old id."""
    live = f"entry1_stale_data_{repairs.mask_vin(_VIN)}"
    assert live not in _swept(_registry(live), [])


def test_another_integrations_issue_is_never_touched() -> None:
    foreign = f"whatever_stale_data_{_VIN}"
    assert _swept(_registry(foreign, domain="some_other_domain"), []) == set()


def test_a_seventeen_character_tail_that_is_not_a_vin_survives() -> None:
    """ISO 3779 excludes I, O and Q. Matching the real alphabet rather than
    ``[A-Z0-9]`` is what keeps this from deleting an unrelated card."""
    not_a_vin = "entry1_something_ABCDEFGHJKLMNOPQR"
    assert not_a_vin not in _swept(_registry(not_a_vin), [])


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (_VIN, True),
        ("WVWZZZAUZFW00000", False),          # 16
        ("WVWZZZAUZFW0000000", False),        # 18
        ("WVWZZZAUZFWO00000", False),         # contains O
        ("***000000", False),                 # the masked form
        ("", False),
    ],
)
def test_the_vin_shape_test_itself(value: str, expected: bool) -> None:
    assert repairs._looks_like_raw_vin(value) is expected


def test_a_broken_registry_does_not_break_setup() -> None:
    """The scan is best-effort: the per-VIN deletes have already run, and a
    registry we cannot walk must degrade to the old behaviour, not raise."""
    hass = MagicMock()
    with patch.object(repairs.ir, "async_get", side_effect=RuntimeError("no registry")), \
            patch.object(repairs.ir, "async_delete_issue") as deleted:
        repairs.sweep_legacy_raw_vin_issues(hass, "entry1", [_VIN])
    assert f"entry1_stale_data_{_VIN}" in {c.args[2] for c in deleted.call_args_list}


def test_the_sweep_is_not_hidden_behind_the_cache_restore() -> None:
    """#923's second hole. The call used to sit inside ``if cached and ...``,
    so an entry with no cached snapshot never swept at all. Pinned
    structurally, because a comment saying "runs on every setup" is exactly
    what was there while it did not."""
    import custom_components.vag_connect.coordinator as coord_mod

    source = pathlib.Path(coord_mod.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    parents: dict[ast.AST, ast.AST] = {}
    call_node = None
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "sweep_legacy_raw_vin_issues"
        ):
            call_node = node
    assert call_node is not None, "the sweep call vanished"

    cur: ast.AST | None = call_node
    guards: list[str] = []
    while cur is not None:
        if isinstance(cur, ast.If):
            guards.append(ast.get_source_segment(source, cur.test) or "")
        cur = parents.get(cur)
    offenders = [g for g in guards if "cached" in g]
    assert offenders == [], (
        f"the sweep is gated on the vehicle cache again, so an entry without a "
        f"cached snapshot never sweeps: {offenders}"
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


# ── the dismissed card, measured on a real registry ───────────────────────
#
# #923 (@skornehl, 2026-10-30) — he measured the sweep on 5.2.0 and reported
# that it removed the legacy card of his sold vehicle, adding: "I had dismissed
# it in the UI, so dismissed cards are covered too."
#
# That works, and it works for a reason outside this repository: dismissing an
# issue in Home Assistant does not remove it. ``IssueRegistry.async_ignore``
# writes the entry back with ``dismissed_version`` set and fires an *update*,
# while the delete path pops the key and fires a *remove*. So the scan still
# sees a dismissed card and deletes it.
#
# The stub registry above cannot pin this: the sweep never looks at an entry's
# VALUE, only at its key, so a stub test would pass whatever the dismissed
# state was and would prove nothing. The assumption that needs guarding is Home
# Assistant's, so these two tests use a REAL ``IssueRegistry`` and will fail if
# an upgrade ever starts removing dismissed issues instead of marking them.


def _real_registry_with_legacy_card(issue_id: str):
    """A real ``IssueRegistry`` carrying one legacy raw-VIN card."""
    from homeassistant.helpers import issue_registry as ha_ir

    registry = ha_ir.IssueRegistry(MagicMock())
    # Persistence is not what these two tests are about, and a mocked hass has
    # no real clock for the debounced store to compare deadlines against.
    registry.async_schedule_save = MagicMock()  # type: ignore[method-assign]
    registry.async_get_or_create(
        DOMAIN,
        issue_id,
        is_fixable=False,
        is_persistent=False,
        severity=ha_ir.IssueSeverity.WARNING,
        translation_key="stale_data",
    )
    return registry, ha_ir


def test_dismissing_a_card_keeps_it_in_the_registry() -> None:
    """The Home-Assistant-side assumption the sweep rests on, pinned against
    the installed package rather than assumed."""
    issue_id = f"entry1_stale_data_{_VIN}"
    registry, _ = _real_registry_with_legacy_card(issue_id)
    key = (DOMAIN, issue_id)
    assert key in registry.issues

    entry = registry.async_ignore(DOMAIN, issue_id, True)
    assert key in registry.issues, (
        "Home Assistant now removes a dismissed issue instead of marking it; "
        "the registry scan in sweep_legacy_raw_vin_issues can no longer reach "
        "a card the user dismissed, and #923 is open again"
    )
    assert entry.dismissed_version is not None

    # Control: the delete path really does remove the key, so the assertion
    # above is testing a difference and not a tautology.
    registry.async_delete(DOMAIN, issue_id)
    assert key not in registry.issues


def test_the_sweep_removes_a_dismissed_legacy_card() -> None:
    """End to end on a real registry: his case, including the dismissal."""
    issue_id = f"entry1_stale_data_{_VIN}"
    registry, _ = _real_registry_with_legacy_card(issue_id)
    registry.async_ignore(DOMAIN, issue_id, True)

    # An empty VIN list, because the car is sold and in no list this code can
    # build — the half of #923 that made the registry scan necessary.
    assert issue_id in _swept(registry, [])
