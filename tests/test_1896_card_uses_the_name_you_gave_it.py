# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""A card that called the car something the owner never called it.

@starwarsfan (#1896) wrote in because the stale-data card titled itself with a
masked VIN alone — unreadable on a two-car account. The first fix routed the
card through the device-name helper so it would "name the vehicle the way the
device page names it".

He checked it on v5.1.1 and it was still wrong, in two ways, and he was right
about both:

1. **The name is not the one he gave the car.** ``_device_name`` builds a name
   out of data — brand plus model, or brand plus the last six VIN characters —
   and never consults Home Assistant's device registry. A device the owner has
   renamed keeps that name in the registry, so his rename was invisible to the
   card. Renaming is an explicit statement about what the car is called; a card
   that overrides it reintroduces the very problem it was built to solve.

2. **It degraded to the bare brand label.** ``Audi (myAudi)`` is what the
   helper returns when it has neither a model nor a VIN. The VIN *is* known at
   that point — it is what raised the card — but the call handed the helper the
   vehicle snapshot instead, and on a snapshot gone thin that key is missing.

The close that preceded this was wrong on its own terms, which is worth saying
in the file rather than only in the thread: it described the design, and his
screenshot showed the implementation.
"""
from __future__ import annotations

import inspect
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from custom_components.vag_connect.coordinator import VagConnectCoordinator


def _coordinator(brand: str = "audi") -> VagConnectCoordinator:
    """A coordinator with just enough shape to call ``_car_label``."""
    coord = VagConnectCoordinator.__new__(VagConnectCoordinator)
    coord.hass = MagicMock()
    coord.entry = SimpleNamespace(entry_id="entry1", data={"brand": brand})
    return coord


def _with_device(device: object | None):
    """Patch the registry lookup to yield ``device``."""
    return patch.object(
        VagConnectCoordinator, "_lookup_own_device", return_value=device
    )


# ── what he actually asked for ─────────────────────────────────────────────


def test_the_name_the_owner_gave_the_car_wins() -> None:
    """The reported case. A rename is an explicit statement; nothing derived
    from data should override it."""
    coord = _coordinator()
    with _with_device(SimpleNamespace(name_by_user="Blauer Q4")):
        label = coord._car_label("WVWZZZAUZFW000000", {"model": "Q4 e-tron"})
    assert label == "Blauer Q4"


def test_a_renamed_car_wins_even_over_a_known_model() -> None:
    """The model is the better *derived* name and still loses. If it did not,
    the rename would only take effect on cars whose model we failed to read —
    which is the opposite of what the owner asked for."""
    coord = _coordinator()
    with _with_device(SimpleNamespace(name_by_user="Der Kombi")):
        label = coord._car_label("WVWZZZAUZFW000000", {"model": "Passat GTE"})
    assert label == "Der Kombi"


@pytest.mark.parametrize("rename", [None, "", "   "])
def test_an_unset_rename_falls_back_rather_than_blanking_the_card(rename) -> None:
    """``name_by_user`` is None until someone renames, and a whitespace-only
    name would title the card with nothing at all."""
    coord = _coordinator()
    with _with_device(SimpleNamespace(name_by_user=rename)):
        label = coord._car_label("WVWZZZAUZFW000000", {"model": "Q4 e-tron"})
    assert label == "Audi Q4 e-tron"


# ── the second fault: the VIN that was known all along ─────────────────────


def test_a_thin_snapshot_still_yields_more_than_the_brand() -> None:
    """His ``Audi (myAudi)``.

    With no model and no ``vin`` key in the snapshot, the old call left the
    helper nothing to work with. The VIN is known here — it is what raised the
    card — so the last six characters are available regardless of what the
    snapshot kept.
    """
    coord = _coordinator()
    with _with_device(None):
        label = coord._car_label("WVWZZZAUZFW000000", {})
    assert label == "Audi 000000", f"degraded to {label!r}"


def test_the_passed_vin_is_used_even_when_the_snapshot_disagrees() -> None:
    """The card is about one VIN. A snapshot carrying a different one — a
    merge artefact, a carried-forward value — must not retitle it."""
    coord = _coordinator()
    with _with_device(None):
        label = coord._car_label("WVWZZZAUZFW000000", {"vin": "WVWZZZAUZFW999999"})
    assert label.endswith("000000"), f"used the snapshot's VIN: {label!r}"


def test_the_full_vin_never_reaches_the_card() -> None:
    """It goes into a user-visible repair card, and from there into
    screenshots posted on a public tracker."""
    coord = _coordinator()
    with _with_device(None):
        label = coord._car_label("WVWZZZAUZFW000000", {})
    assert "WVWZZZAUZFW" not in label


# ── it must not be able to suppress the warning ────────────────────────────


def test_a_broken_registry_costs_the_name_and_not_the_warning() -> None:
    """Naming a car is a courtesy; the card is the point. If the registry
    cannot be read, the label degrades and the warning still fires."""
    coord = _coordinator()
    with patch.object(
        VagConnectCoordinator, "_lookup_own_device", side_effect=RuntimeError("boom")
    ):
        label = coord._car_label("WVWZZZAUZFW000000", {"model": "Q4 e-tron"})
    assert label == "Audi Q4 e-tron"


def test_the_lookup_is_wrapped() -> None:
    """Pinned at the source as well, because the behavioural test above only
    proves the one exception it raises. A registry read is exactly the kind of
    call that grows a new failure mode across Home Assistant versions."""
    src = inspect.getsource(VagConnectCoordinator._car_label)
    assert "try:" in src and "except Exception" in src, (
        "the registry lookup is no longer guarded; a registry error would now "
        "stop the stale-data card from being raised at all"
    )


def test_it_uses_the_entry_scoped_lookup_helper() -> None:
    """Not ``async_get_device(identifiers=...)`` directly.

    That form is deprecated in HA 2026.9 and breaks in 2027.8 because
    identifiers are no longer unique across config entries. The repository
    already has ``_lookup_own_device``, which scopes to this entry and falls
    back on older cores — a second, unguarded call site would rot silently.
    """
    src = inspect.getsource(VagConnectCoordinator._car_label)
    assert "_lookup_own_device" in src
    assert "async_get_device(identifiers" not in src


def test_the_card_asks_for_the_label() -> None:
    """The fix is only worth anything if the caller uses it.

    ``_enrich``, not ``_poll_loop`` — the first version of this asserted
    against the latter and failed for the wrong reason, which is its own small
    lesson about asserting on a method you have not looked up. The name is
    derived from the source here rather than written down, so moving the call
    to another method fails this test instead of silently passing it.
    """
    import ast
    import pathlib

    import custom_components.vag_connect.coordinator as coord_mod

    source = pathlib.Path(coord_mod.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    holders = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and "self._car_label(" in (ast.get_source_segment(source, node) or "")
    ]
    assert holders, (
        "nothing calls _car_label any more, so a renamed car is invisible to "
        "the stale-data card again"
    )
    assert "_enrich" in holders, f"the call moved out of _enrich: {holders}"
    src = inspect.getsource(VagConnectCoordinator._enrich)
    assert "self._car_label(_vin_sd, data)" in src, (
        "the card no longer passes the VIN that raised it, so a thin snapshot "
        "can degrade the title back to the bare brand label"
    )
