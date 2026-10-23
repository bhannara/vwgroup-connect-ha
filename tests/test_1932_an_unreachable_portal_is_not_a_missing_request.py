# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""#1932/#1933/#1915 — a portal we could not reach was reported as a portal
that told us the data request is missing.

**Measured, not inferred.** On 2026-10-22 VW let the EU Data Act portal's TLS
certificate expire (``NotAfter`` 23:59:59 UTC; renewed by ~08:25 UTC the next
morning). aiohttp raises ``ClientConnectorCertificateError`` for that, which is
a ``ClientConnectionError`` subclass, so every poll landed in the transport
handler of ``_get_json``. That handler returned ``None`` *without* touching
``_last_soft_status``, so the caller could not tell the two cases apart and
took the only branch it had:

    "no data-request yet … enable the continuous data request for this car"

The advice was the exact opposite of the truth. The request was alive and still
producing files, and users deleted working requests on the strength of that
sentence — one said so in #1932 and had to recreate it. The listing leg had the
same hole one step later, where an unreachable portal was filed as ``empty``:
"the portal answered and had nothing for us", which is the opposite of what
happened.

The axis these tests sit on is the one this integration keeps failing on: can
the reader tell a failure on VW's side from a failure of their own? So each
test below pins a cause to the reason code AND to the advice, and the 404 and
no-identifier cases are pinned just as hard — a fix that reclassified a genuine
"not provisioned yet" as an outage would be the same bug pointing the other
way.

The last group covers #1915 (@scoma24), who hit this from the other end: the
strategy log named the exception class but dropped the HTTP status, so
"raised UpstreamUnavailableError (message redacted)" was all the reporter had
to tell a VW 5xx from a client-side fault. They asked for the status by hand.
"""
from __future__ import annotations

import asyncio
import logging
import ssl
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.vag_connect.cariad.auth._eu_data_act import (
    EUDataActConnector,
)
from custom_components.vag_connect.cariad.exceptions import (
    UpstreamUnavailableError,
)

_VIN = "WVWZZZAAAA0000001"
_IDENT = "aaaaaaaa1111bbbb2222cccc3333dddd"  # 32 hex, as the portal issues them
_MODULE = "custom_components.vag_connect.cariad.auth._eu_data_act"
_SLEEP = f"{_MODULE}.asyncio.sleep"
_HOST = "eu-data-act.portal.invalid"


# ── the failures VW actually produced ──────────────────────────────────────


def _expired_certificate() -> aiohttp.ClientConnectorCertificateError:
    """The 2026-10-22 outage, as aiohttp reports it.

    Built from the real class rather than a stand-in: the whole defect was a
    question of which ``except`` clause this lands in, and a hand-rolled
    exception would answer that question by assumption.
    """
    key = MagicMock()
    key.host, key.port, key.is_ssl = _HOST, 443, True
    return aiohttp.ClientConnectorCertificateError(
        key,
        ssl.SSLCertVerificationError(
            "certificate verify failed: certificate has expired"
        ),
    )


def _resp(*, status: int = 200, json_data: Any = None) -> AsyncMock:
    r = AsyncMock()
    r.status = status
    r.json = AsyncMock(return_value=json_data)
    r.text = AsyncMock(return_value="")
    r.read = AsyncMock(return_value=b"")
    r.__aenter__ = AsyncMock(return_value=r)
    r.__aexit__ = AsyncMock(return_value=False)
    return r


def _raising(exc: BaseException) -> AsyncMock:
    """A ``session.get(...)`` whose ``__aenter__`` raises — no response at all,
    which is what a transport or TLS failure looks like from the caller."""
    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(side_effect=exc)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


class _Portal:
    """Routes by URL, like the real portal's two legs.

    Each leg takes a payload, an ``int`` status, or an exception instance. A
    plain class and not a MagicMock on purpose: ``_get_json`` guards on
    ``getattr(session, "closed", False) is True``, and a mock's auto-created
    ``.closed`` is truthy, which would make every call here return early.
    """

    def __init__(self, *, meta: Any, listing: Any = None) -> None:
        self._meta, self._listing = meta, listing
        self.urls: list[str] = []

    def get(self, url: str, **_kw: Any) -> Any:
        self.urls.append(url)
        if "metadata" in url:
            return self._leg(self._meta)
        if url.endswith("/list"):
            return self._leg(self._listing)
        raise AssertionError(f"unexpected GET {url}")

    @staticmethod
    def _leg(spec: Any) -> Any:
        if isinstance(spec, BaseException):
            return _raising(spec)
        if isinstance(spec, int):
            return _resp(status=spec)
        return _resp(json_data=spec)


def _poll(
    *, meta: Any, listing: Any = None
) -> tuple[EUDataActConnector, _Portal]:
    sess = _Portal(meta=meta, listing=listing)
    conn = EUDataActConnector(sess, brand="volkswagen")  # type: ignore[arg-type]
    with patch(_SLEEP, new=AsyncMock()):  # the real backoff is 3 s + 6 s
        asyncio.run(conn.get_vehicle_data(_VIN))
    return conn, sess


_LIVE_META = [{"Frequency": "15mins", "Identifier": _IDENT}]


# ── the metadata leg: an outage must not read as a missing request ─────────


def test_an_expired_portal_certificate_is_not_a_missing_data_request() -> None:
    """The reported case, end to end."""
    conn, _ = _poll(meta=_expired_certificate())
    assert conn.last_no_data_reason == "portal_error", (
        "an unreachable portal is still classified as "
        f"{conn.last_no_data_reason!r} — portal_error is the reason that "
        "already means 'VW-side outage', and the coordinator maps it to the "
        "portal_error health state"
    )


def test_it_does_not_tell_the_user_to_enable_a_request_that_exists(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The sentence that cost people their data requests."""
    with caplog.at_level(logging.INFO, logger=_MODULE):
        _poll(meta=_expired_certificate())
    text = caplog.text
    assert "enable the continuous data request" not in text, (
        "the outage path still advises enabling a data request; that advice is "
        "what made users delete the working one in #1932"
    )
    assert "do not change or delete it" in text, (
        "the outage path no longer tells the user to leave the request alone"
    )


def test_the_outage_message_does_not_blame_the_account(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Two reporters checked their consent settings for nothing."""
    with caplog.at_level(logging.INFO, logger=_MODULE):
        _poll(meta=_expired_certificate())
    assert "not a problem with your account" in caplog.text


def test_the_outage_message_names_the_exception_class(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """#1915's ask, on this leg: the reader needs to know WHAT failed."""
    with caplog.at_level(logging.INFO, logger=_MODULE):
        _poll(meta=_expired_certificate())
    assert "ClientConnectorCertificateError" in caplog.text


def test_the_outage_message_never_carries_the_exception_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """``str()`` of an aiohttp connector error carries the host it dialled, and
    the portal URL embeds the VIN. Only the class name is recorded — asserted
    here because storing ``str(err)`` is the obvious, wrong shortcut."""
    conn, _ = _poll(meta=_expired_certificate())
    assert conn._last_soft_transport_error == "ClientConnectorCertificateError"
    with caplog.at_level(logging.INFO, logger=_MODULE):
        _poll(meta=_expired_certificate())
    assert _HOST not in caplog.text
    assert "certificate verify failed" not in caplog.text


@pytest.mark.parametrize(
    "exc",
    [
        TimeoutError("portal slow"),
        aiohttp.ClientConnectionError("connection reset"),
        aiohttp.ServerDisconnectedError(),
    ],
    ids=["timeout", "connection-reset", "server-disconnected"],
)
def test_every_transport_failure_is_an_outage(exc: BaseException) -> None:
    """The certificate was one way in. The handler takes a whole family, and
    none of its members say anything about the user's data request."""
    conn, _ = _poll(meta=exc)
    assert conn.last_no_data_reason == "portal_error"


# ── the other direction: a real "not provisioned" must stay that ───────────


def test_a_portal_that_answers_404_is_still_a_missing_request() -> None:
    """A 404 IS the portal answering "no such request". Reclassifying it as an
    outage would hide the one case where the user does have something to do."""
    conn, _ = _poll(meta=404)
    assert conn.last_no_data_reason == "no_request"


def test_a_404_still_gets_the_advice_that_helps(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO, logger=_MODULE):
        _poll(meta=404)
    assert "enable the continuous data request" in caplog.text


def test_a_portal_that_answers_without_an_identifier_is_a_missing_request() -> None:
    """The portal replied, and its reply named no active request."""
    conn, _ = _poll(meta={})
    assert conn.last_no_data_reason == "no_request"


def test_a_404_does_not_set_the_transport_flag() -> None:
    """The two channels must not contradict each other: a leg that got an HTTP
    response has, by definition, not failed in transport."""
    conn, _ = _poll(meta=404)
    assert conn._last_soft_transport_error is None


# ── the listing leg, one step later ────────────────────────────────────────


def test_an_unreachable_listing_is_an_outage_not_an_empty_delivery() -> None:
    """``empty`` claims the portal answered and had nothing. It did not answer."""
    conn, sess = _poll(meta=_LIVE_META, listing=_expired_certificate())
    assert any(u.endswith("/list") for u in sess.urls), (
        "the listing leg was never reached, so this test proves nothing about it"
    )
    assert conn.last_no_data_reason == "portal_error"


def test_an_unreachable_listing_says_which_class_failed(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """It used to print "(HTTP n/a)", which reads like a portal quirk rather
    than a connection that never happened."""
    with caplog.at_level(logging.INFO, logger=_MODULE):
        _poll(meta=_LIVE_META, listing=_expired_certificate())
    assert "ClientConnectorCertificateError" in caplog.text
    assert "HTTP n/a" not in caplog.text


def test_a_404_listing_is_still_delivery_not_ready() -> None:
    """The counter-case on this leg: a 404 here means the request exists and
    has not delivered yet, which is a normal wait, not a fault."""
    conn, _ = _poll(meta=_LIVE_META, listing=404)
    assert conn.last_no_data_reason == "empty"


def test_a_5xx_listing_is_still_an_outage() -> None:
    """Pre-existing behaviour (#465), re-pinned because the new condition was
    added to the same expression and could have displaced it."""
    conn, _ = _poll(meta=_LIVE_META, listing=503)
    assert conn.last_no_data_reason == "portal_error"


# ── the flag must not outlive the failure it describes ─────────────────────


def test_the_flag_is_cleared_once_the_portal_answers_again() -> None:
    """A flag that stuck would turn every later "not provisioned" into a false
    outage report — the same defect with the sign flipped."""
    sess = _Portal(meta=_expired_certificate())
    conn = EUDataActConnector(sess, brand="volkswagen")  # type: ignore[arg-type]
    with patch(_SLEEP, new=AsyncMock()):
        asyncio.run(conn.get_vehicle_data(_VIN))
    assert conn._last_soft_transport_error == "ClientConnectorCertificateError"

    conn._session = _Portal(meta=404)  # type: ignore[assignment]
    with patch(_SLEEP, new=AsyncMock()):
        asyncio.run(conn.get_vehicle_data(_VIN))
    assert conn._last_soft_transport_error is None
    assert conn.last_no_data_reason == "no_request", (
        "a cleared portal is reporting an outage from a previous poll"
    )


def test_a_fresh_connector_starts_with_no_transport_failure() -> None:
    conn = EUDataActConnector(_Portal(meta={}), brand="volkswagen")  # type: ignore[arg-type]
    assert conn._last_soft_transport_error is None


# ── #1915: the strategy log has to name the status it already holds ────────


def _client_whose_strategies_raise(err: BaseException) -> Any:
    """A real ``VWEUClient`` with every login strategy raising *err*.

    Lifted from ``test_1855_a_backend_outage_is_not_a_wrong_password.py``,
    which pins the sibling behaviour of this same ``except`` block, so both
    tests exercise the real strategy list rather than a stub of it.
    """
    from custom_components.vag_connect.cariad.api.vw_eu import VWEUClient

    c = VWEUClient(MagicMock(), "u@t.de", "pw")

    async def _boom(*_a: Any, **_k: Any) -> Any:
        raise err

    c._auth.authenticate = _boom  # the "idk" strategies
    c._arm_eu_portal = _boom  # the data_act_portal fallback
    return c


def _authenticate(c: Any) -> None:
    with pytest.raises(BaseException):  # noqa: B017, PT011 - raising is the point
        asyncio.run(c.authenticate())


def test_the_strategy_log_names_the_http_status(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """#1915 — the reporter got the class and had to ask for the status."""
    with caplog.at_level(logging.WARNING):
        _authenticate(_client_whose_strategies_raise(
            UpstreamUnavailableError(503, "volkswagen")
        ))
    assert "UpstreamUnavailableError" in caplog.text
    assert "HTTP 503" in caplog.text, (
        "the status is carried on the exception as .status and is not a "
        "secret; without it the log cannot separate a VW 5xx from a "
        "client-side fault"
    )


def test_a_foreign_exception_is_still_redacted(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Why the redaction exists in the first place: an aiohttp error's text can
    carry the OAuth callback URL, whose JWTs decode to a live token. Appending
    a status must not have re-opened that."""
    url = "weconnect://authenticated#access_token=eyJsecret"
    with caplog.at_level(logging.WARNING):
        _authenticate(_client_whose_strategies_raise(ValueError(f"Invalid URL {url}")))
    assert "ValueError" in caplog.text
    assert "access_token" not in caplog.text
    assert "weconnect://" not in caplog.text


def test_an_exception_without_a_status_logs_no_status(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Most exceptions have no status, and inventing one ("HTTP None") would be
    noise in the common case."""
    with caplog.at_level(logging.WARNING):
        _authenticate(_client_whose_strategies_raise(ValueError("plain")))
    assert "HTTP" not in caplog.text
