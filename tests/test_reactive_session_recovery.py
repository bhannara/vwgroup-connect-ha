# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""What actually recovers a session that cannot renew itself.

Some sign-in paths leave a session with no renewable token: the credential
expires and the only way back is a fresh sign-in. A v2.8.0 watchdog was built
to notice that from the outside — every car stale and failing for twice the
poll interval — and sign in again before the next poll. It never ran once, and
it was removed rather than switched on; ``test_strategy_labels_are_paired.py``
holds the reason.

Removing it only makes sense if what remains actually covers the condition, and
this file is that evidence. It drives the reactive path end to end with the HTTP
layer faked rather than the recovery, which is the one shape that can tell
"recovery works" apart from "recovery is wired up".

**That distinction is worth the file.** A read-only survey of four comparable
projects in this field found that not one of them has such a test: their
recovery tests stub the client, or stub the very function whose behaviour is
being asserted, so they pin the wiring and not the recovery. The same survey
found no proactive staleness watchdog anywhere in the field either — the
reactive path plus escalation is the whole of the field's answer, which is the
strongest argument that removing ours was right rather than merely harmless.

The third case below is the honest half. A 401 is recovered; a **403** is not,
and this module's own constants say why: an expired bearer can come back 403
rather than 401 from that backend, which is the entire reason a proactive
re-mint exists at all. That re-mint is gated on one strategy, so for the
sessions the watchdog was meant to serve there is no 403 coverage. Pinning it
here turns a gap that was discovered twice into one that is stated.
"""
from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock

import pytest

from custom_components.vag_connect.cariad.api.vw_eu import VWEUClient
from custom_components.vag_connect.cariad.exceptions import (
    APIError,
    AuthenticationError,
)
from custom_components.vag_connect.cariad.models import TokenSet

_URL = "https://example.invalid/vehicles"


def _resp(status: int, payload: Any = None) -> AsyncMock:
    r = AsyncMock()
    r.status = status
    # The success path returns parsed JSON only when the header says so, and
    # falls back to raw text otherwise. A mock without this returns "" and the
    # assertion below would be measuring the mock, not the client.
    r.headers = {"Content-Type": "application/json"}
    r.json = AsyncMock(return_value=payload if payload is not None else {})
    r.text = AsyncMock(return_value="")
    r.read = AsyncMock(return_value=b"")
    r.__aenter__ = AsyncMock(return_value=r)
    r.__aexit__ = AsyncMock(return_value=False)
    return r


class _Wire:
    """The HTTP layer, faked. Serves a scripted sequence of statuses and counts
    how many requests were actually sent."""

    def __init__(self, *statuses: int) -> None:
        self._statuses = list(statuses)
        self.sent = 0

    def request(self, method: str, url: str, **kw: Any) -> Any:
        self.sent += 1
        status = self._statuses.pop(0) if self._statuses else 200
        return _resp(status, {"ok": True})


def _client(wire: _Wire) -> tuple[VWEUClient, list[int]]:
    """A client on an UNRENEWABLE session, with the sign-in instrumented.

    ``refresh_token=""`` is the shape that matters: it is what the sign-in
    flows the watchdog targeted leave behind, so ``_refresh_tokens`` has no
    renewal branch to take and must fall through to a full sign-in.
    """
    c = VWEUClient(wire, "u@t.de", "pw")
    c._tokens = TokenSet(
        access_token="EXPIRED", refresh_token="", id_token="i",
        expires_at=0.0, strategy="",
    )
    sign_ins: list[int] = []

    async def _authenticate() -> None:
        sign_ins.append(1)
        c._tokens = TokenSet(
            access_token="FRESH", refresh_token="", id_token="i",
            expires_at=0.0, strategy="",
        )

    c.authenticate = _authenticate  # type: ignore[method-assign]
    return c, sign_ins


# ── the condition the watchdog was built for, recovered reactively ─────────


def test_an_expired_session_recovers_on_the_failing_request() -> None:
    """The whole case for deleting the watchdog.

    A 401 on a read drives one sign-in and one retry, and the read succeeds —
    without waiting for every car to be stale for twice the poll interval,
    which is what the watchdog would have waited for.
    """
    wire = _Wire(401, 200)
    c, sign_ins = _client(wire)

    out = asyncio.run(c._request("GET", _URL))

    assert out == {"ok": True}
    assert sign_ins == [1], f"expected exactly one sign-in, got {len(sign_ins)}"
    assert wire.sent == 2, "one failing request plus one retry"
    assert c._tokens.access_token == "FRESH"
    assert len(c._refresh_history) == 1, "the sign-in was billed to the budget"


def test_recovery_does_not_loop_when_the_retry_also_fails() -> None:
    """The bound. A session that cannot be recovered must escalate, not retry.

    The survey that prompted this file found a project whose equivalent loop
    sends roughly six sign-in-capable requests per burst, once a minute,
    indefinitely, whenever the failure persists past a successful sign-in. Ours
    must stop at one.
    """
    wire = _Wire(401, 401)
    c, sign_ins = _client(wire)

    # Measured, and worth naming: a 401 that survives the sign-in surfaces as a
    # plain APIError, NOT as an authentication error. So it does not itself
    # escalate to Home Assistant's re-authentication prompt from here - the
    # field's own answer to an unrecoverable session leans on that escalation,
    # and whether ours arrives by another route is a separate question than
    # this file settles.
    with pytest.raises(APIError) as caught:
        asyncio.run(c._request("GET", _URL))
    assert caught.value.status == 401
    assert not isinstance(caught.value, AuthenticationError)

    assert sign_ins == [1], (
        f"a failure that survived the sign-in produced {len(sign_ins)} sign-ins; "
        "one is the bound"
    )
    assert wire.sent == 2, "no third attempt"


def test_the_sign_in_is_billed_so_a_storm_is_refused() -> None:
    """Recovery shares the hourly budget rather than having its own allowance.

    This is what the removed watchdog did NOT do: it called the sign-in
    directly, outside this accounting. Four recoveries in an hour must cost
    four slots and then be refused, not proceed.
    """
    from custom_components.vag_connect.cariad.api import base as _base

    c, sign_ins = _client(_Wire())

    async def _spend() -> None:
        for _ in range(_base._REFRESH_MAX_PER_HOUR):
            await c._refresh_tokens()
        with pytest.raises(AuthenticationError):
            await c._refresh_tokens()

    asyncio.run(_spend())

    assert len(sign_ins) == _base._REFRESH_MAX_PER_HOUR
    assert c.refresh_storm_detected is True, (
        "the storm flag drives the repair that tells the user; recovery must "
        "not be able to churn silently"
    )


# ── the honest half: what the reactive path does NOT cover ────────────────


def test_a_403_does_not_recover_and_that_is_the_known_gap() -> None:
    """Pinned so it is a stated gap rather than one found a third time.

    This module's constants say an expired bearer can come back 403 rather than
    401 from that backend, which is why a proactive re-mint exists — and that
    re-mint is gated on a single strategy plus a stored password, so it does not
    cover the unrenewable sessions this file is about. If someone widens 403
    handling later, this test fails and should be rewritten rather than deleted:
    the fact to keep is which statuses recover, not that 403 does not.
    """
    wire = _Wire(403, 200)
    c, sign_ins = _client(wire)

    with pytest.raises(Exception) as caught:  # noqa: PT011 - class asserted below
        asyncio.run(c._request("GET", _URL))

    assert sign_ins == [], (
        "a 403 now triggers a sign-in; that is a behaviour change, and the "
        "proactive re-mint gated on one strategy exists because it did not"
    )
    assert wire.sent == 1, "no retry on 403"
    assert "403" in str(caught.value) or getattr(caught.value, "status", None) == 403


def test_the_proactive_remint_is_still_gated_to_one_strategy() -> None:
    """The counter-fact for the gap above, so the two are read together.

    The re-mint that does cover an expired-bearer-as-403 is reachable only for
    one strategy with a stored password. Asserted at the source rather than
    described, because the gap statement above is only true while this is.
    """
    import inspect

    from custom_components.vag_connect.cariad.api import base as _base

    src = inspect.getsource(_base.CariadBaseClient._request)
    idx = src.index("_DEVICE_GRANT_REMINT_SKEW_S")
    window = src[max(0, idx - 900):idx + 200]
    assert 'strategy", "") == "device_grant"' in window
    assert "self._vweu_password" in window, (
        "the proactive re-mint is no longer gated on a stored password; the "
        "403 gap above may have narrowed and both tests need re-reading"
    )
