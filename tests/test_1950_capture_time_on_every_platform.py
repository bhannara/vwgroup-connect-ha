# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""#1950 (@Adcad1970) — a door state needs a capture time as much as a reading.

Per-value freshness (``data_captured_at`` / ``freshness_source`` /
``ambiguous_reading``) shipped in v4.7.11 on ``VagConnectSensor`` only. So a
numeric sensor could say "captured 15:36" while the closure and lock binary
sensors beside it — doors, locks, windows, boot, bonnet — said nothing at all.
On a portal-fed car those states are carried forward between snapshots, so a
door state captured six hours ago renders identically to one captured a minute
ago, and nothing on the entity lets anyone tell them apart.

The worst case this guards: a carried-forward "doors closed" sitting next to a
fresh battery reading on the same dashboard. The owner reads the fresh stamp,
assumes it covers the row, and walks away from an unlocked car.

The fix moves the method onto ``VagConnectEntity``, where the shared
``extra_state_attributes`` already merges per-platform attributes. No platform
file was touched to gain it, which is the point: the gate
(``field_sources[data_key] == "eu_data_act"``) does the limiting itself, so a
live-read channel and a description without a ``data_key`` still get nothing.

The second half of #1950 is a correction rather than a feature. The docstring of
``_capture_age_s`` claimed ``last_seen_at`` "says when the delivery was last
SEEN". It does not — every writer of that field in this tree takes a capture
stamp — and that sentence was the source of a public statement that had to be
withdrawn. A test pins it, because a wrong comment reproduces itself.
"""
from __future__ import annotations

import ast
import pathlib
from typing import Any
from unittest.mock import MagicMock

import pytest

from custom_components.vag_connect.binary_sensor import (
    BINARY_DESCRIPTIONS,
    VagConnectBinarySensor,
)
from custom_components.vag_connect.entity_base import VagConnectEntity
from custom_components.vag_connect.sensor import VagConnectSensor

_PKG = pathlib.Path(__file__).resolve().parents[1] / "custom_components/vag_connect"

_DOOR_TS = "2026-10-27T15:36:00+00:00"
_FRESH_TS = "2026-10-27T19:58:16+00:00"


def _desc(key: str):
    """The REAL shipped description for ``key`` — not a stand-in.

    A hand-built description would pass even if the real one lost its
    ``data_key``, which is the whole hinge of the gate.
    """
    for d in BINARY_DESCRIPTIONS:
        if d.key == key:
            return d
    raise AssertionError(f"no shipped binary description for {key!r}")


def _entity(cls: type, description: Any, vehicle: dict) -> Any:
    """A real entity of ``cls`` with its real description, constructor bypassed.

    ``__init__`` wants a live coordinator; the property under test wants only
    ``coordinator.data``, ``_vin``, ``_key`` and ``entity_description``. Going
    through ``__new__`` keeps the class, the MRO and the real description
    genuine while leaving the constructor out of the measurement.
    """
    ent = cls.__new__(cls)
    ent.coordinator = MagicMock()
    ent.coordinator.data = {"V": vehicle}
    ent._vin = "V"
    ent._key = getattr(description, "key", "k")
    ent.entity_description = description
    return ent


def _portal_door(
    *, captured: dict[str, str] | None = None, key: str = "doors_open"
) -> Any:
    vehicle: dict[str, Any] = {
        "doors_open": False,
        "doors_locked": True,
        "battery_soc": 52,
        "field_sources": {
            "doors_open": "eu_data_act",
            "doors_locked": "eu_data_act",
            "battery_soc": "eu_data_act",
        },
    }
    if captured is not None:
        vehicle["field_captured_ts"] = captured
    return _entity(VagConnectBinarySensor, _desc(key), vehicle)


class TestTheClosureSensorsFinallyCarryTheirCaptureTime:
    def test_a_portal_fed_door_carries_its_own_capture_time(self) -> None:
        attrs = _portal_door(captured={"doors_open": _DOOR_TS}).extra_state_attributes
        assert attrs is not None
        assert attrs["data_captured_at"] == _DOOR_TS
        assert attrs["freshness_source"] == "point"

    def test_the_door_does_not_borrow_a_fresher_fields_stamp(self) -> None:
        """The exact confusion #1950 is about: the newest stamp in the feed is
        not this field's stamp. The door must report 15:36, not 19:58."""
        attrs = _portal_door(
            captured={"doors_open": _DOOR_TS, "battery_soc": _FRESH_TS}
        ).extra_state_attributes
        assert attrs is not None
        assert attrs["data_captured_at"] == _DOOR_TS
        assert attrs["data_captured_at"] != _FRESH_TS

    def test_the_lock_entity_gets_it_too_not_just_the_door(self) -> None:
        attrs = _portal_door(
            captured={"doors_locked": _DOOR_TS}, key="doors_locked"
        ).extra_state_attributes
        assert attrs is not None
        assert attrs["data_captured_at"] == _DOOR_TS

    def test_without_a_genuine_stamp_it_says_dataset_and_invents_nothing(self) -> None:
        attrs = _portal_door(captured=None).extra_state_attributes
        assert attrs is not None
        assert attrs["freshness_source"] == "dataset"
        assert "data_captured_at" not in attrs

    def test_a_stamp_for_another_field_only_still_says_dataset(self) -> None:
        attrs = _portal_door(captured={"battery_soc": _FRESH_TS}).extra_state_attributes
        assert attrs is not None
        assert attrs["freshness_source"] == "dataset"
        assert "data_captured_at" not in attrs


class TestTheGateStillLimitsItself:
    def test_a_live_channel_door_carries_no_freshness_at_all(self) -> None:
        """A live read's poll time IS its capture time, so the attributes would
        say nothing. This is why no platform needed a hand-picked entity list."""
        ent = _entity(
            VagConnectBinarySensor,
            _desc("doors_open"),
            {
                "doors_open": False,
                "field_sources": {"doors_open": "mbb"},
                "field_captured_ts": {"doors_open": _DOOR_TS},
            },
        )
        attrs = ent.extra_state_attributes or {}
        assert "data_captured_at" not in attrs
        assert "freshness_source" not in attrs

    def test_an_entity_without_a_data_key_gets_no_freshness(self) -> None:
        """Buttons, images and the device tracker carry descriptions with no
        ``data_key``. Reaching through one must not raise and must not invent."""

        class _NoKey(VagConnectEntity):
            def __init__(self) -> None:
                self.coordinator = MagicMock()
                self.coordinator.data = {"V": {"field_sources": {"": "eu_data_act"}}}
                self._vin = "V"
                self._key = "k"

        assert _NoKey()._eu_da_freshness_attributes() == {}

    def test_no_field_sources_at_all_is_survivable(self) -> None:
        ent = _entity(
            VagConnectBinarySensor, _desc("doors_open"), {"doors_open": True}
        )
        assert ent._eu_da_freshness_attributes() == {}


class TestNothingElseChanged:
    def test_the_platforms_own_attributes_survive_beside_the_capture_time(self) -> None:
        """``VagConnectBinarySensor`` already had a ``_platform_attributes``
        hook for the OTA release-notes URL. Gaining freshness must not cost it."""
        ent = _entity(
            VagConnectBinarySensor,
            _desc("ota_update_available"),
            {
                "ota_update_available": True,
                "ota_release_notes_url": "https://example.invalid/notes",
                "software_update_status": "readyForUpdate",
                "field_sources": {"ota_update_available": "eu_data_act"},
                "field_captured_ts": {"ota_update_available": _DOOR_TS},
            },
        )
        attrs = ent.extra_state_attributes
        assert attrs is not None
        assert attrs["release_notes_url"] == "https://example.invalid/notes"
        assert attrs["raw_status"] == "readyForUpdate"
        assert attrs["data_captured_at"] == _DOOR_TS

    def test_the_sensor_platform_still_carries_the_same_three_keys(self) -> None:
        """Parity guard for the move: the sensor platform is where this already
        worked, so it is the half that could regress silently."""
        ent = _entity(
            VagConnectSensor,
            MagicMock(key="battery_soc", data_key="battery_soc"),
            {
                "battery_soc": 52,
                "field_sources": {"battery_soc": "eu_data_act"},
                "field_captured_ts": {"battery_soc": _FRESH_TS},
                "ambiguous_fields": {"battery_soc": "two candidates"},
            },
        )
        attrs = ent.extra_state_attributes
        assert attrs is not None
        assert attrs["data_captured_at"] == _FRESH_TS
        assert attrs["freshness_source"] == "point"
        assert attrs["ambiguous_reading"] is True

    def test_a_platform_attribute_still_wins_a_name_clash(self) -> None:
        """Order was base-then-platform before the move and must stay so, or a
        platform that deliberately overrides a shared name loses silently."""

        class _Collide(VagConnectEntity):
            def __init__(self) -> None:
                self.coordinator = MagicMock()
                self.coordinator.data = {
                    "V": {
                        "field_sources": {"battery_soc": "eu_data_act"},
                        "field_captured_ts": {"battery_soc": _FRESH_TS},
                    }
                }
                self._vin = "V"
                self._key = "k"
                self.entity_description = MagicMock(data_key="battery_soc")

            def _platform_attributes(self) -> dict[str, Any]:
                return {"freshness_source": "platform-says-so"}

        assert _Collide().extra_state_attributes["freshness_source"] == "platform-says-so"


class TestOneImplementationOnly:
    def test_the_freshness_logic_is_defined_exactly_once(self) -> None:
        """Two copies of this method is how the two sensor platforms drifted
        apart in the first place. Catch the next copy, in any platform file."""
        found = []
        for path in sorted(_PKG.glob("*.py")):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if (
                            isinstance(item, ast.FunctionDef)
                            and item.name == "_eu_da_freshness_attributes"
                        ):
                            found.append(f"{path.name}::{node.name}")
        assert found == ["entity_base.py::VagConnectEntity"], (
            f"per-value freshness must live on the shared base exactly once, "
            f"or the platforms drift apart again. Found: {found}"
        )

    @pytest.mark.parametrize("cls", [VagConnectSensor, VagConnectBinarySensor])
    def test_every_platform_inherits_it_from_the_base(self, cls: type) -> None:
        owner = next(
            c for c in cls.__mro__ if "_eu_da_freshness_attributes" in c.__dict__
        )
        assert owner is VagConnectEntity, f"{cls.__name__} shadows it again"


class TestTheDeliveryClockClaimIsGone:
    """The comment half of #1950.

    Read from the source FILE, deliberately not through ``inspect.getsource``:
    a stale ``__pycache__`` can hand ``getsource`` the previous text and a
    docstring test then reports on code that no longer exists.
    """

    def test_the_docstring_no_longer_calls_last_seen_at_a_delivery_clock(self) -> None:
        text = (_PKG / "coordinator.py").read_text(encoding="utf-8")
        assert "says when the delivery was last SEEN" not in text, (
            "the false characterisation is back: last_seen_at is a capture "
            "stamp on every channel that writes it, never a delivery clock"
        )
        assert "the delivery sighting, i.e. the previous behaviour" not in text

    def test_the_docstring_says_what_it_actually_is(self) -> None:
        text = (_PKG / "coordinator.py").read_text(encoding="utf-8")
        # Single-line anchors on purpose: a multi-line anchor also pins the
        # line wrapping, so reflowing the paragraph would fail a test that has
        # nothing to say about wrapping.
        assert "delivery clock." in text
        assert "takes a CAPTURE stamp" in text
        assert "the car's freshest capture across channels" in text

    def test_no_writer_of_last_seen_at_uses_a_wall_clock(self) -> None:
        """The claim the docstring now makes, measured instead of asserted.

        Every assignment to ``last_seen_at`` must come from a capture stamp. A
        writer that assigned ``utcnow()`` or a poll time would make the old
        docstring right and this whole correction wrong, so the claim is worth
        a test rather than a sentence.
        """
        offenders = []
        for path in sorted(_PKG.rglob("*.py")):
            for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#") or "last_seen_at" not in stripped:
                    continue
                if "=" not in stripped or "==" in stripped or "!=" in stripped:
                    continue
                target, _, value = stripped.partition("=")
                if "last_seen_at" not in target:
                    continue
                if any(
                    token in value
                    for token in ("utcnow", "now()", "time.time", "dt_util.utcnow")
                ):
                    offenders.append(f"{path.name}:{i}: {stripped}")
        assert offenders == [], (
            f"a writer anchors last_seen_at on a wall clock, which contradicts "
            f"the corrected docstring: {offenders}"
        )
