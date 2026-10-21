# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Six characters of a VIN, frozen into an entity id forever.

@benbrummer (#1801) confirmed the volkswagen.de channel works on his
Commercial Vehicles T6.1 — and reported, alongside that, an entity whose id
embeds part of his VIN while its friendly name reads correctly.

Both halves of that are components behaving as designed. Home Assistant
derives an ``entity_id`` once, from the device name at the moment the entity is
first created, and never touches it again; this integration never rewrites one
either — its only registry write is ``new_unique_id``. The friendly name is
recomputed from live data on every update, which is why it corrected itself
and the id did not.

So whichever entity spawns **first** fixes that id forever, and the one that
spawned first was the push event entity — the only platform that needed no
data to exist. At that moment ``_device_name`` has no model to work with and
falls back to ``"{Brand} {VIN[-6:]}"``. Every other entity waits for a field,
gets the real model, and is named properly. The single platform that needed no
data met the single naming path that needs data.

The fix is that the event entity now waits for there to have *been* a poll —
not for any particular field, which would change what the event stream is for.
``[]`` is the spawner's documented "not ready yet" answer and it re-evaluates
on every coordinator update, so the entity appears one poll later with the
model name known.

**Deliberately not fixed by dropping the VIN fallback.** On an account with two
cars and no model data yet, those six characters are the only thing telling the
devices apart — removing them would trade a frozen id for two
indistinguishable devices.

His own entity keeps its id; that is his to rename if he wants to, and he was
told so. This is about the next person's first setup.
"""
from __future__ import annotations

import inspect

from custom_components.vag_connect import entity_base, event as event_mod


def test_the_event_entity_waits_for_the_first_poll() -> None:
    """The fix, read where it is made."""
    src = inspect.getsource(event_mod.async_setup_entry)
    assert "if not vehicle:" in src, (
        "the event entity no longer waits for data, so it can spawn before "
        "the device can be named and freeze a VIN fragment into its id again"
    )
    assert "return []" in src


def test_it_is_not_gated_on_a_particular_field() -> None:
    """The distinction that keeps the event stream's purpose intact: it waits
    for a poll, not for a value. Gating it on, say, a charging field would
    silently remove the event entity from cars that never report one."""
    src = inspect.getsource(event_mod.async_setup_entry)
    marker = src.index("if not vehicle:")
    guard = src[marker:marker + 120]
    for field in ("battery_soc", "is_charging", "model", "odometer"):
        assert field not in guard, (
            f"the event entity is now gated on {field!r}; it must wait for a "
            "poll, not for a particular reading"
        )


def test_the_vin_fallback_is_still_there() -> None:
    """Not the thing to fix. It is the only disambiguator between two cars on
    one account before any model name is known."""
    src = inspect.getsource(entity_base._device_name)
    assert "vin[-6:]" in src, (
        "the VIN fallback is gone; two cars with no model data would now get "
        "the same device name"
    )


def test_the_device_name_prefers_the_model() -> None:
    """And the fallback stays a fallback: with a model present it must not be
    reached, which is what makes waiting one poll sufficient."""
    # The brand label is title-cased by the helper, so assert on the shape
    # rather than on a hand-written string — the first version of this guessed
    # "volkswagen …" and failed on the capital.
    named = entity_base._device_name(
        {"vin": "WVWZZZAUZFW000000", "model": "T6.1 Transporter"}, "volkswagen"
    )
    assert named.endswith("T6.1 Transporter")
    assert "000000" not in named, "the model is known, so no VIN fragment"
    # and without one, the fallback — with only the last six, never the whole VIN
    fallback = entity_base._device_name(
        {"vin": "WVWZZZAUZFW000000"}, "volkswagen"
    )
    assert fallback.endswith("000000")
    assert "WVWZZZAUZFW" not in fallback, "the full VIN is in the device name"


def test_the_integration_never_rewrites_an_entity_id() -> None:
    """The premise that makes this preventable-only-at-creation.

    If a later version did start renaming entity ids, the whole shape of this
    fix would change — and someone should learn that from a failing test
    rather than from a user whose automations broke.
    """
    import pathlib

    import custom_components.vag_connect as pkg

    offenders: list[str] = []
    for path in pathlib.Path(pkg.__file__).parent.rglob("*.py"):
        for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "async_update_entity(" in stripped and "new_entity_id" in stripped:
                offenders.append(f"{path.name}:{idx}")
    assert not offenders, (
        f"the integration now rewrites entity ids at {offenders}; re-check "
        "whether the first-spawn naming still matters"
    )
