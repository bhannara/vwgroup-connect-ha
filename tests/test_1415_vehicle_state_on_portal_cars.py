# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""A Vehicle Status sensor that was blank on every portal-fed car.

@theblarney1 (Discussion #1415) runs a portal-fed CUPRA Tavascan and reported
**Vehicle Status** permanently unknown. The public diagnosis at the time said
the sensor had exactly one writer — the CUPRA online-services call his car
answers with 403 — and that it only wrote while the engine was running.

**All three of those specifics were wrong**, and the real cause is wider:

* the key is ``vehicle_state``, and it has **two** writers, not one;
* the one that governs his car is the ``_enrich`` derivation in the
  coordinator, which is **channel-agnostic** and runs for every brand;
* there is no engine-running gate in it.

``_enrich`` stamps OFFLINE / DRIVING / CHARGING / PARKED, and the PARKED branch
required ``is_online is True``. Measured: the EU Data Act portal writes
``is_online`` **zero** times, so ``online`` is always None on a portal-fed car
and none of the four branches could fire. It does write the other two
affirmatively — ``is_driving`` True/False from the standstill signal and
``is_charging`` from the charging state. So the sensor was blank not on
CUPRA/SEAT but on **every portal-fed car of every brand**, including
Volkswagen and Audi.

The fix adds one branch for the case the feed actually describes: online
unknown, and the car affirmatively neither driving nor charging. It uses
``is False`` identity checks rather than falsy tests, because a falsy test
would also match ``None`` and stamp PARKED on a car that said nothing — the
fabrication the never-guess rule forbids. The last row of the truth table
still yields unknown, and that is pinned in ``test_coordinator.py`` beside the
#923 guarantee it belongs with.
"""
from __future__ import annotations

import asyncio
import inspect

import pytest

from custom_components.vag_connect import coordinator as coord_mod


def _enrich(data: dict) -> dict:
    """Run the real ``_enrich`` against a bare coordinator.

    Mirrors the idiom the existing TestEnrich cases use, so this file cannot
    drift from how that derivation is exercised elsewhere.
    """
    from tests.test_coordinator import TestEnrich

    coord = TestEnrich()._make_coord()
    return asyncio.run(coord._enrich(data))


#: What a portal-fed car's snapshot looks like: no online flag, both activity
#: signals present and negative.
PORTAL_PARKED = {
    "is_online": None,
    "is_driving": False,
    "is_charging": False,
    "latitude": None,
    "longitude": None,
}


# ── his case ───────────────────────────────────────────────────────────────


def test_a_parked_portal_car_reports_parked() -> None:
    """This returned unknown before, forever, on every portal car."""
    assert _enrich(dict(PORTAL_PARKED))["vehicle_state"] == "PARKED"


def test_it_is_not_reported_as_offline() -> None:
    """The #923 guarantee this must not undo: unknown online is not offline."""
    assert _enrich(dict(PORTAL_PARKED))["vehicle_state"] != "OFFLINE"


# ── the never-fabricate rule survives ──────────────────────────────────────


@pytest.mark.parametrize(
    "driving,charging",
    [(None, None), (False, None), (None, False)],
    ids=["nothing known", "only standstill", "only charging"],
)
def test_nothing_affirmative_stays_unknown(driving, charging) -> None:
    """Identity checks are the whole safety of this fix. A falsy test would
    match None and claim PARKED on silence."""
    data = dict(PORTAL_PARKED, is_driving=driving, is_charging=charging)
    assert _enrich(data).get("vehicle_state") is None


def test_the_branch_uses_identity_checks_not_falsy_tests() -> None:
    """Pinned at the source as well as behaviourally.

    The behavioural tests above would also pass with ``not data.get(...)`` for
    the ``(False, None)`` rows if the ordering happened to work out, and the
    distinction is too easy to 'simplify' away later. The reason it must stay
    is written where the change is.
    """
    src = inspect.getsource(coord_mod.VagConnectCoordinator._enrich)
    assert 'data.get("is_driving") is False' in src
    assert 'data.get("is_charging") is False' in src


# ── the other states still win ─────────────────────────────────────────────


def test_driving_and_charging_still_take_precedence() -> None:
    """The new branch is last for a reason: an active signal outranks a
    standstill derivation.

    ``plug_connected=True`` is required for the charging case and is not
    padding. On a cloud channel ``_enrich`` clears a charging claim whenever
    the plug is not known to be connected (the #32 guard: "when plug is
    disconnected, charging MUST be False"), so a fixture that merely says
    ``is_charging=True`` has its claim withdrawn before the state chain runs,
    and then reads PARKED. The first version of this test omitted it and
    failed with exactly that — which is a better outcome than it passing,
    because the interaction is now written down.
    """
    assert _enrich(dict(PORTAL_PARKED, is_driving=True))["vehicle_state"] == "DRIVING"
    assert _enrich(
        dict(PORTAL_PARKED, is_charging=True, plug_connected=True)
    )["vehicle_state"] == "CHARGING"
    assert _enrich(dict(PORTAL_PARKED, is_online=False))["vehicle_state"] == "OFFLINE"


def test_a_withdrawn_charging_claim_reads_parked_not_unknown() -> None:
    """The interaction above, pinned deliberately rather than as a surprise.

    A cloud car claiming to charge with no plug information has that claim
    cleared by the #32 guard. The result is an affirmative "not charging", so
    PARKED is the honest reading of it — and it is the same treatment such a
    car already got when ``is_online`` was True. This fix extends that to the
    online-unknown case rather than inventing a new rule for it.
    """
    out = _enrich(dict(PORTAL_PARKED, is_charging=True))
    assert out["is_charging"] is False, "the #32 plug guard no longer fires"
    assert out["vehicle_state"] == "PARKED"


def test_a_state_the_client_already_set_is_not_overwritten() -> None:
    """``_enrich`` only derives when the field is empty — the SEAT/CUPRA client
    writes DRIVING itself, and that must stand."""
    data = dict(PORTAL_PARKED, vehicle_state="DRIVING")
    assert _enrich(data)["vehicle_state"] == "DRIVING"


# ── the premise, so a feed change fails here first ─────────────────────────


def test_the_portal_still_never_sends_is_online() -> None:
    """The whole reason the PARKED branch could not fire. If the portal ever
    starts sending it, this fix becomes unnecessary rather than wrong — but
    someone should find that out from a failing test, not by guessing."""
    from custom_components.vag_connect.cariad.auth import _eu_data_act as eda

    src = inspect.getsource(eda)
    assert "d.is_online" not in src, (
        "the portal mapper now writes is_online; re-check whether the #1415 "
        "branch is still needed"
    )
    # control: the fields it DOES write are found by the same search
    assert "d.is_driving" in src and "d.is_charging" in src
