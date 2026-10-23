# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""#584 — a refusal whose cause had been measured was still filed as "unknown".

@panther7's log carried the two halves side by side, and they disagreed:

    INFO  command_unlock(***) classified as unknown
    ERROR command_unlock(***) failed: VehicleCommandError (status=None) — the
          car's gateway accepted your S-PIN and then refused this integration's
          client identity for commands. This is not your password, your S-PIN
          or your subscription — all three checked out.

The prose was right. It comes from the code that read the gateway's body. The
enum beside it was wrong: ``classify_command_failure`` bails out to ``UNKNOWN``
for any exception that is not an ``APIError``, and the gateway refusal is
wrapped in a ``VehicleCommandError``, which is not one and carries no body. So
the function answered before looking at anything the exception held — while
``raise_if_leg3_refusal`` had computed the kind four lines earlier and kept only
the prose.

A reader who sees "classified as unknown" directly above a precise explanation
learns to distrust both lines. That is the whole of the harm here, and this file
says so rather than overclaiming: nothing in the integration reads
``FeatureState.last_error``, so making the stat truthful changes no behaviour by
itself.

**The part that needed care, and the reason this is not a one-line change.**
The obvious target member was ``ATTESTATION_LOCKED`` — its docstring reads
almost like the leg-3 prose. It is also one of three members that set
``entitled_by_account = False``, which ``is_command_known_unsupported`` turns
into ``available = False`` for 24 hours. Reusing it would have taken
@panther7's Lock control offline for a day to fix a log line, on a reporter
whose controls are visible today. So the measured cause gets a member that
records it and touches nothing: ``CLIENT_IDENTITY_REFUSED``. The second half of
this file exists to keep it that way, and to pin the contrast against a member
that really does hide.
"""
from __future__ import annotations

import pytest

from custom_components.vag_connect.cariad.api.vw_eu import raise_if_leg3_refusal
from custom_components.vag_connect.cariad.exceptions import (
    APIError,
    CommandFailureReason,
    SpinError,
    VehicleCommandError,
    classify_command_failure,
)

_VIN = "WVWZZZAAAA0000001"
# The marker @panther7's lock refusal actually carried, and nothing else we
# were matching (leg3_refusal_kind).
_CLIENT_IDENTITY_BODY = '{"error":{"code":"RS.security.9007","msg":"forbidden"}}'
_SCHEMA_BODY = '{"error":{"code":"gw.error.validation"}}'


def _refusal(body: str) -> VehicleCommandError:
    """Drive the REAL raiser, not a hand-built exception.

    The defect was that the raiser discarded what it knew, so a test that
    constructed the exception itself would assert nothing about the raiser and
    would keep passing if it went back to discarding.
    """
    err = APIError(403, "https://example.invalid/commands", body)
    with pytest.raises(VehicleCommandError) as caught:
        raise_if_leg3_refusal(err, "command_lock")
    return caught.value


class _Coord:
    """A coordinator reduced to the two methods under test, built the way
    ``TestFeatureStateTracking`` in test_cariad.py builds one."""

    def __new__(cls):  # noqa: D102
        from custom_components.vag_connect.coordinator import VagConnectCoordinator

        coord = VagConnectCoordinator.__new__(VagConnectCoordinator)
        coord.feature_states = {}
        return coord


# ── the reported defect ────────────────────────────────────────────────────


def test_the_reported_refusal_is_no_longer_unknown() -> None:
    """The exact line from his log, end to end through the real raiser."""
    exc = _refusal(_CLIENT_IDENTITY_BODY)
    assert classify_command_failure(exc) is (
        CommandFailureReason.CLIENT_IDENTITY_REFUSED
    ), (
        "the gateway's refusal is still filed as 'cause unknown', directly "
        "above a message that names the cause"
    )


def test_the_raiser_stops_discarding_what_it_measured() -> None:
    """``leg3_refusal_kind`` returns a structured kind and the raise used to
    keep only the prose. Both halves must now travel together."""
    exc = _refusal(_CLIENT_IDENTITY_BODY)
    assert exc.failure_reason is CommandFailureReason.CLIENT_IDENTITY_REFUSED
    assert "client identity" in exc.reason, (
        "the prose is the half the user reads and must not have been traded away"
    )


def test_the_schema_refusal_carries_its_own_cause() -> None:
    """The other measured kind. Its own comment at the raise says the account IS
    allowed to send this and the car's older schema is what rejects it, which is
    what WRONG_API_PROFILE means."""
    exc = _refusal(_SCHEMA_BODY)
    assert classify_command_failure(exc) is CommandFailureReason.WRONG_API_PROFILE


# ── the availability guarantee: this must change nothing a user sees ───────


@pytest.mark.parametrize(
    "reason",
    [
        CommandFailureReason.CLIENT_IDENTITY_REFUSED,
        CommandFailureReason.WRONG_API_PROFILE,
    ],
    ids=["client-identity-refused", "wrong-api-profile"],
)
def test_recording_a_measured_cause_does_not_take_the_control_offline(
    reason: CommandFailureReason,
) -> None:
    """THE test of this change. Both members must leave every flag alone, so
    the only thing that moves is the log line and the recorded stat."""
    coord = _Coord()
    coord.record_command_failure(_VIN, "command_lock", reason)
    state = coord.get_feature_state(_VIN, "command_lock")

    assert state.last_error is reason, "the stat did not become truthful"
    assert state.supported_by_vehicle is None
    assert state.entitled_by_account is None
    assert state.retry_after is None
    assert coord.is_command_known_unsupported(_VIN, "command_lock") is False, (
        "a log-line fix just made the Lock control unavailable"
    )


@pytest.mark.parametrize(
    "body", [_CLIENT_IDENTITY_BODY, _SCHEMA_BODY], ids=["client-identity", "schema"]
)
def test_the_whole_path_leaves_the_control_available(body: str) -> None:
    """The chain, not its links — and the one a mutation check had to find.

    The two tests above both pass even if the raiser is changed to attach a
    member that hides the control: one drives the raiser and only looks at the
    label, the other hands a label straight to the recorder and never goes near
    the raiser. Neither sees a wrong mapping in between.

    This walks the whole path @panther7's Lock press takes — gateway body, the
    raiser, the classifier, the recorder, availability — so a mapping changed at
    any point along it fails here.
    """
    coord = _Coord()
    exc = _refusal(body)

    coord.record_command_failure(_VIN, "command_lock", classify_command_failure(exc))

    state = coord.get_feature_state(_VIN, "command_lock")
    assert state.entitled_by_account is None
    assert state.supported_by_vehicle is None
    assert coord.is_command_known_unsupported(_VIN, "command_lock") is False, (
        "recording this measured refusal takes the Lock control offline for 24 "
        "hours — which is a change to what the user sees, not a log-line fix"
    )


def test_the_member_we_deliberately_did_not_reuse_does_hide() -> None:
    """The contrast, pinned. ATTESTATION_LOCKED reads like the leg-3 prose and
    was the obvious choice; it is also one of the three members that take the
    control offline for 24 h. This asserts the behaviour we avoided, so the
    reason for avoiding it cannot quietly stop being true."""
    coord = _Coord()
    coord.record_command_failure(
        _VIN, "command_lock", CommandFailureReason.ATTESTATION_LOCKED
    )
    state = coord.get_feature_state(_VIN, "command_lock")

    assert state.entitled_by_account is False
    assert state.retry_after is not None
    assert coord.is_command_known_unsupported(_VIN, "command_lock") is True


def test_the_new_member_is_outside_both_flag_flipping_branches() -> None:
    """Said once more at the level of the whole enum, because the next person
    adding a member will look for exactly this list. Only these four touch a
    flag; everything else records and returns."""
    hiding = set()
    for reason in CommandFailureReason:
        coord = _Coord()
        coord.record_command_failure(_VIN, "command_lock", reason)
        if coord.is_command_known_unsupported(_VIN, "command_lock"):
            hiding.add(reason)

    assert hiding == {
        CommandFailureReason.MISSING_CAPABILITY,
        CommandFailureReason.SUBSCRIPTION_EXPIRED,
        CommandFailureReason.NOT_ENTITLED,
        CommandFailureReason.ATTESTATION_LOCKED,
    }, f"the set of members that take a control offline changed: {hiding}"
    assert CommandFailureReason.CLIENT_IDENTITY_REFUSED not in hiding


# ── everything that must classify exactly as before ────────────────────────


def test_an_error_that_measured_nothing_is_still_unknown() -> None:
    """The conservative default is the whole reason this function exists. Most
    of the roughly forty-six raise sites never measured a cause, and inventing
    one for them would be worse than saying so."""
    assert classify_command_failure(
        VehicleCommandError("command_lock", "it just failed")
    ) is CommandFailureReason.UNKNOWN


def test_a_stray_attribute_is_not_believed() -> None:
    """The check is on the TYPE of the carried value, not merely its presence,
    so an unrelated exception carrying a same-named attribute cannot inject a
    verdict where callers expect a member."""
    exc = VehicleCommandError("command_lock", "x")
    exc.failure_reason = "attestation_locked"  # type: ignore[assignment]
    assert classify_command_failure(exc) is CommandFailureReason.UNKNOWN


def test_the_locally_raised_spin_error_still_wins() -> None:
    """SpinError is special-cased above the gate and above the new check; its
    own issue (#666) exists because it used to surface as an UNKNOWN crash."""
    assert classify_command_failure(SpinError("no S-PIN configured")) is (
        CommandFailureReason.SPIN_REQUIRED
    )


def test_an_api_error_still_classifies_from_its_body() -> None:
    """Nothing below the new check moved. The body table is untouched."""
    assert classify_command_failure(
        APIError(403, "u", '{"error":{"message":"missing-capability"}}')
    ) is CommandFailureReason.MISSING_CAPABILITY


def test_a_bare_403_still_reads_as_not_entitled() -> None:
    """Unchanged — and it is also the measurement that decided the design.

    The tempting broad fix was to follow ``__cause__`` from the wrapper to the
    gateway's ``APIError`` and classify its body, which would have covered every
    raise site at once. But the leg-3 markers are not in this function's body
    table, so that 403 falls through to here, and NOT_ENTITLED is one of the
    members that takes the control offline for 24 h — while the prose the user
    reads says their subscription checked out. The broad fix would have been
    worse than the defect.
    """
    assert classify_command_failure(
        APIError(403, "u", _CLIENT_IDENTITY_BODY)
    ) is CommandFailureReason.NOT_ENTITLED


def test_every_existing_raise_site_keeps_working_positionally() -> None:
    """The new argument is keyword-only with a default, so none of the existing
    sites across five modules needed touching — asserted rather than assumed,
    because a positional break would surface as a crash inside a command."""
    exc = VehicleCommandError("command_lock", "prose only")
    assert exc.command == "command_lock"
    assert exc.reason == "prose only"
    assert exc.failure_reason is None
    with pytest.raises(TypeError):
        VehicleCommandError(  # type: ignore[misc]
            "command_lock", "prose", CommandFailureReason.UNKNOWN
        )


def test_an_unmeasured_body_still_propagates_untouched() -> None:
    """``raise_if_leg3_refusal`` returns without raising for a body it has not
    measured, so the caller re-raises the original. Hiding an unmeasured failure
    behind a reassuring sentence is the thing its docstring forbids."""
    err = APIError(403, "https://example.invalid/commands", '{"error":"something new"}')
    assert raise_if_leg3_refusal(err, "command_lock") is None
