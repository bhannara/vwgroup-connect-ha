# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""A Battery level sensor that could never fill.

@keylogicjohan's ID.7 (#1902) sends the pack's energy content and no state of
charge. Once #1905 taught the drivetrain derivation to read that energy content
as evidence of a drive battery, his electric entities appeared — and **Battery
level** appeared with them, permanently empty, because the field it reads is
one his feed never sends. @bercedev deliberately left that out of the fix
rather than widening a ten-line change into a design argument, which was the
right call; this is the follow-up.

``battery_soc`` was the odd one out of its own family. ``electric_range_km``,
``battery_available_kwh`` and ``battery_cap_kwh`` were already in
``_DATA_PRESENT_REQUIRED``, the set of keys whose entity is not created until
the field is actually present, so a car that does not publish them gets no
phantom "unknown" row. ``battery_soc`` was not in it.

**Why that is safe for every other EV**, which is the question this change
turns on: ``register_dynamic_spawner`` re-evaluates the build on every
coordinator update and tracks what it has already added, so — in its own
words — a sensor gated this way "still spawns the moment its value arrives".
A normal EV gets Battery level on the first poll that carries a state of
charge and keeps it; a restored snapshot carries ``battery_soc`` forward, so an
existing entry has it at setup. Only a car that never sends one is spared the
empty row.
"""
from __future__ import annotations

import inspect

from custom_components.vag_connect import sensor as sensor_mod


def test_battery_soc_requires_data_to_be_present() -> None:
    """The fix."""
    assert "battery_soc" in sensor_mod._DATA_PRESENT_REQUIRED


def test_its_family_is_gated_the_same_way() -> None:
    """The reason this is a correction rather than a new policy: the other
    electric headline fields were already gated, and ``battery_soc`` being
    outside the set was the inconsistency."""
    for key in (
        "electric_range_km",
        "battery_available_kwh",
        "battery_cap_kwh",
    ):
        assert key in sensor_mod._DATA_PRESENT_REQUIRED, key


def test_the_sensor_is_still_electric_conditioned() -> None:
    """Gating on data must not replace the drivetrain condition. A combustion
    car should not get a Battery level entity even if some field happened to
    be present."""
    descs = [
        d for d in sensor_mod.SENSOR_DESCRIPTIONS
        if getattr(d, "data_key", None) == "battery_soc"
    ]
    assert descs, "no sensor description reads battery_soc any more"
    assert any(getattr(d, "condition", None) == "electric" for d in descs), (
        "battery_soc lost its electric condition; a combustion car would now "
        "be eligible for a Battery level entity"
    )


def test_the_spawner_still_promises_to_add_it_later() -> None:
    """The premise that makes the gate safe rather than a regression.

    If the spawner ever stops re-evaluating, this gate turns into "no Battery
    level until you restart Home Assistant" for every EV, which is far worse
    than one empty row on one car. That is worth failing a test over.
    """
    from custom_components.vag_connect import entity_base

    src = inspect.getsource(entity_base.register_dynamic_spawner)
    assert "re-evaluated on every coordinator update" in src, (
        "the dynamic spawner no longer documents re-evaluating; the "
        "data-present gate depends on it"
    )
    # and the mechanism, not just the sentence: it tracks what it added
    assert "added" in src and "unique_id" in src


def test_the_gate_is_not_quietly_widened() -> None:
    """``_DATA_PRESENT_REQUIRED`` is a per-key opt-in by design — its own
    comment says most sensors legitimately start as None and should NOT be
    gated. A change that swept in a whole family would be a different
    decision from this one."""
    src = inspect.getsource(sensor_mod)
    marker = "_DATA_PRESENT_REQUIRED: frozenset[str] = frozenset({"
    block = src[src.index(marker):]
    block = block[:block.index("\n})")]
    keys = [ln.strip().strip('",') for ln in block.splitlines() if ln.strip().startswith('"')]
    assert "battery_soc" in keys
    # a sanity bound: this set is large but finite, and a sudden jump would
    # mean someone added a loop rather than a key
    assert 300 < len(keys) < 420, f"{len(keys)} keys — unexpected size"
