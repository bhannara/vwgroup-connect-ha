# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""#1918 — a refresh that cannot possibly work was paying for itself out of the
hourly budget, and the retries that mattered were refused for lack of it.

**Measured, not inferred.** @georghaberkorn68-ctrl captured two consecutive
polls of a CUPRA on a 3600 s interval. The entry was on the read-only EU Data
Act portal fallback, which installs a SENTINEL ``TokenSet``: a literal
placeholder as the ``access_token`` and an empty ``refresh_token``, so
``TokenSet.is_valid()`` — which only tests both strings for non-emptiness —
reports the client as authenticated while there is nothing to authenticate with.

The native backend answers 401 to that placeholder. Each 401 entered
``_request``'s retry branch, which called ``_refresh_tokens``: a budget slot was
booked, the refresh branch was skipped for want of a refresh token, the full
re-login ran the whole sign-in chain, landed on the same fallback, and
reinstalled the same sentinel. The retry then 401'd exactly as before.

A portal-mode poll makes three native reads — one charging-profiles plus two
battery-care in a single gather — so the whole ``_REFRESH_MAX_PER_HOUR`` budget
was gone inside ONE poll. Fourteen minutes later his drop-retries were refused:

    Token refresh budget spent: 3 attempts in the last 3600s for cupra (data)
    Charging-profiles fetch failed for ***: AuthenticationError

Neither read arms its one-hour cache on the failure path, so it repeated on
every poll, indefinitely.

**Why #1078's single-flight guard did not contain it.** That guard returns only
when the token CHANGED while the caller queued. These sentinels are constant
literals, so after a "successful" re-login the ``access_token`` is byte-identical
to the stale one the waiter captured — the guard never fires, and the two
concurrent battery-care 401s both booked. The sentinel disables the very guard
that exists to stop one event eating the budget. ``test_1078_refresh_coalesce``
pins that guard; this file pins the case it cannot see.

The second half of this file is the half that matters for review: five of the
seven strategies in the tree must be completely unaffected, including
``hybrid_full``, whose own docstring says it relies on an empty refresh token
falling through to a full re-login. A fix that silenced that would trade a
budget leak for a dead channel.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any
from unittest.mock import AsyncMock

import pytest

from custom_components.vag_connect.cariad.api import base as _base
from custom_components.vag_connect.cariad.api.vw_eu import VWEUClient
from custom_components.vag_connect.cariad.auth import _mbboauth
from custom_components.vag_connect.cariad.exceptions import (
    AuthenticationError,
    TokenRefreshRetryError,
)
from custom_components.vag_connect.cariad.models import TokenSet

_MODULE = "custom_components.vag_connect.cariad.api.base"

# The two literals the fallback channels actually install (base.py).
_PORTAL_SENTINEL = "eu-data-act-portal-cookie-session"
_AUTHPROXY_SENTINEL = "vw-website-authproxy-cookie-session"


class _Sess:
    def get(self, url: str, headers: Any = None) -> Any:  # pragma: no cover
        raise AssertionError("no network in these tests")


class _RefreshWasAttempted(Exception):
    """Raised from the stub the moment a real token rotation hits the wire."""


class _PostReached(_Sess):
    def post(self, *a: Any, **k: Any) -> Any:
        raise _RefreshWasAttempted


def _client(
    *, access_token: str, refresh_token: str, strategy: str
) -> VWEUClient:
    c = VWEUClient(_Sess(), "u@t.de", "pw")
    c._tokens = TokenSet(
        access_token=access_token,
        refresh_token=refresh_token,
        id_token=access_token,
        expires_at=0.0,
        strategy=strategy,
    )
    # A full re-login is the expensive thing this fix refuses to pay for, so
    # every test watches it rather than trusting the budget count alone.
    c.authenticate = AsyncMock(return_value=None)  # type: ignore[method-assign]
    return c


def _portal_client() -> VWEUClient:
    return _client(
        access_token=_PORTAL_SENTINEL, refresh_token="", strategy="data_act_portal"
    )


# ── the defect ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("sentinel", "strategy"),
    [
        (_PORTAL_SENTINEL, "data_act_portal"),
        (_AUTHPROXY_SENTINEL, "website_authproxy"),
    ],
    ids=["eu-data-act-portal", "website-authproxy"],
)
def test_a_cookie_session_refresh_spends_no_budget(
    sentinel: str, strategy: str
) -> None:
    """Both fallback channels install the same shape of sentinel, so both had
    the same leak. The portal one is what #1918 measured; the authproxy one is
    the same code path and is pinned so it cannot be fixed for one and left
    open for the other."""
    c = _client(access_token=sentinel, refresh_token="", strategy=strategy)

    asyncio.run(c._refresh_tokens(stale_access_token=sentinel))

    assert c._refresh_history == [], (
        "a refresh that cannot produce a token still booked a budget slot"
    )
    c.authenticate.assert_not_awaited()
    assert c.refresh_storm_detected is False


def test_the_reported_poll_leaves_the_whole_budget_intact() -> None:
    """The headline. His poll made three native reads; each 401 booked a slot,
    and the retries fourteen minutes later were then refused. Three refusals
    must now cost nothing, and the budget must still be fully available."""
    c = _portal_client()

    async def _one_poll() -> None:
        # one charging-profiles read, then two battery-care reads in a gather
        await c._refresh_tokens(stale_access_token=_PORTAL_SENTINEL)
        await asyncio.gather(
            c._refresh_tokens(stale_access_token=_PORTAL_SENTINEL),
            c._refresh_tokens(stale_access_token=_PORTAL_SENTINEL),
        )

    asyncio.run(_one_poll())

    assert len(c._refresh_history) == 0
    assert len(c._refresh_history) < _base._REFRESH_MAX_PER_HOUR, (
        "the budget is partly spent, so a later drop-retry can still be refused"
    )
    assert c.refresh_storm_detected is False, (
        "the storm flag would raise a 'raise your update interval' repair, and "
        "at 3600 s the interval was never the problem"
    )


def test_it_repeats_without_cost_because_the_failure_path_repeats() -> None:
    """Neither native read arms its one-hour cache when it fails, so this fires
    on every poll for as long as the fallback is live. Many polls, no cost."""
    c = _portal_client()

    async def _many() -> None:
        for _ in range(3 * 12):  # twelve polls' worth
            await c._refresh_tokens(stale_access_token=_PORTAL_SENTINEL)

    asyncio.run(_many())

    assert c._refresh_history == []
    c.authenticate.assert_not_awaited()


def test_the_refusal_returns_rather_than_raising() -> None:
    """The caller's retry frame is unchanged by this fix: it re-sends, 401s, and
    raises as it always did. Raising here instead would have changed the shape
    the callers already swallow and turned a quiet degradation into an error."""
    c = _portal_client()
    assert asyncio.run(c._refresh_tokens(stale_access_token=_PORTAL_SENTINEL)) is None


def test_the_command_plane_budget_is_also_spared() -> None:
    """Commands bill a separate budget (#584). A sentinel cannot serve a command
    either, so the refusal must cover both planes rather than only reads."""
    c = _portal_client()
    asyncio.run(c._refresh_tokens(for_command=True))
    assert c._cmd_refresh_history == []
    assert c._refresh_history == []


# ── the channels that must keep working ────────────────────────────────────


def test_an_empty_refresh_token_alone_still_re_authenticates() -> None:
    """THE collateral case. ``hybrid_full`` sets no strategy of its own, so its
    token set carries ``strategy=""`` and an empty refresh token, and
    ``authenticate()``'s docstring says it relies on exactly that falling
    through to a full re-login every ~2 h. Keying the refusal on the empty
    refresh token alone would have killed that channel silently."""
    c = _client(access_token="REAL_BEARER", refresh_token="", strategy="")

    asyncio.run(c._refresh_tokens())

    c.authenticate.assert_awaited_once()
    assert len(c._refresh_history) == 1, "a real re-login must still be billed"


def test_a_portal_strategy_with_a_real_refresh_token_is_not_refused() -> None:
    """The conjunction is deliberate. ``device_grant_portal`` is portal-ish by
    name but carries a real bearer and a real refresh token, and its own branch
    in ``_refresh_tokens`` rotates it and re-injects it into the connector.
    Refusing by name would have broken a working channel."""
    c = _client(
        access_token="REAL_BEARER",
        refresh_token="RT",
        strategy="device_grant_portal",
    )
    # It reaches the device-grant branch and genuinely attempts the rotation,
    # which then fails on this test's offline session. That failure is the
    # PROOF: a refused refresh would never have got far enough to try.
    with pytest.raises(TokenRefreshRetryError, match="Device grant refresh"):
        asyncio.run(c._refresh_tokens())
    assert len(c._refresh_history) == 1, (
        "a channel with a real refresh token was refused as if it had none"
    )
    c.authenticate.assert_not_awaited()


def test_a_listed_strategy_holding_a_real_refresh_token_is_not_refused() -> None:
    """The other half of the conjunction, and the half a mutation check found
    missing from this file.

    The refusal asks TWO questions: is this one of the bearer-less channels, and
    does it in fact have nothing to refresh. Only the second is load-bearing —
    which is the useful property, because it means the strategy list cannot
    silently refuse a channel that could have worked. Asserted with a token
    shape that does not exist in the tree today precisely so that, if one of
    these channels ever gains a real refresh token, this file says what must
    happen rather than leaving it to be rediscovered.
    """
    c = _client(
        access_token="REAL_BEARER", refresh_token="RT", strategy="data_act_portal"
    )
    # The marker proves the refusal did not short-circuit: a refused refresh
    # returns before any network call, so reaching the wire at all is the
    # assertion. Asserting on whatever the offline stub happens to raise would
    # pin an accident instead.
    c._session = _PostReached()  # type: ignore[assignment]
    c._auth._session = _PostReached()  # type: ignore[attr-defined]

    with pytest.raises(_RefreshWasAttempted):
        asyncio.run(c._refresh_tokens())

    assert len(c._refresh_history) == 1, (
        "a listed strategy was refused on its name alone, even though it had a "
        "refresh token to spend"
    )
    c.authenticate.assert_not_awaited()


def test_a_real_mbb_refresh_still_rotates_and_bills(monkeypatch) -> None:
    """The durable MBB channel: a real bearer, a real refresh recipe. Untouched."""
    c = _client(access_token="STALE", refresh_token="RT", strategy="mbb")
    c._mbb_client_id = "CID"
    calls: list[int] = []

    async def _fake(session, refresh_token, *, client_id):
        calls.append(1)
        return _mbboauth.MbbTokenSet(
            access_token="NEW", refresh_token="RT",
            token_type="Bearer", expires_at=0.0,
        )

    monkeypatch.setattr(_mbboauth, "refresh", _fake)

    asyncio.run(c._refresh_tokens(stale_access_token="STALE"))

    assert calls == [1]
    assert len(c._refresh_history) == 1
    assert c._tokens.access_token == "NEW"


def test_the_storm_guard_still_trips_for_a_real_token() -> None:
    """The budget must keep doing its job where it is the right answer. Nothing
    about this fix touches a token that could genuinely be refreshed."""
    c = _client(access_token="REAL_BEARER", refresh_token="", strategy="")

    async def _hammer() -> None:
        for _ in range(_base._REFRESH_MAX_PER_HOUR):
            await c._refresh_tokens()
        with pytest.raises(AuthenticationError):
            await c._refresh_tokens()

    asyncio.run(_hammer())

    assert len(c._refresh_history) == _base._REFRESH_MAX_PER_HOUR
    assert c.refresh_storm_detected is True


def test_the_single_flight_guard_still_wins_when_the_token_rotated() -> None:
    """#1078's guard sits above the new one and must keep its precedence: a
    waiter whose token was already rotated returns without billing, and that is
    true whatever the strategy is."""
    c = _client(access_token="NEW_BEARER", refresh_token="RT", strategy="mbb")
    asyncio.run(c._refresh_tokens(stale_access_token="OLD_BEARER"))
    assert c._refresh_history == []
    c.authenticate.assert_not_awaited()


# ── the scope decision, pinned rather than remembered ──────────────────────


def test_only_the_two_bearer_less_channels_are_listed() -> None:
    """Pinned so widening this is a deliberate act. Every other strategy in the
    tree carries a real bearer: ``device_grant``, ``device_grant_portal``,
    ``mbb``, ``porsche``, and ``""`` for the classic/hybrid flows. Adding one of
    those here would refuse a refresh that works."""
    assert _base._COOKIE_SESSION_STRATEGIES == (
        "data_act_portal",
        "website_authproxy",
    )


def test_the_sentinels_still_look_like_the_constant_expects() -> None:
    """The refusal keys on the strategy name, but it is only correct because
    those two channels install a bearer-less sentinel. If a future edit gave
    either one a real token, this refusal would start suppressing a refresh that
    could have worked — so the premise is asserted against the source that
    produces it, not left to memory."""
    import inspect

    src = inspect.getsource(_base)
    for strategy, sentinel in (
        ("data_act_portal", _PORTAL_SENTINEL),
        ("website_authproxy", _AUTHPROXY_SENTINEL),
    ):
        idx = src.index(f'access_token="{sentinel}"')
        window = src[idx:idx + 400]
        assert 'refresh_token=""' in window, (
            f"the {strategy} sentinel no longer has an empty refresh_token; the "
            "refusal in _refresh_tokens assumes it has nothing to refresh"
        )
        assert f'strategy="{strategy}"' in window


# ── the log has to be findable, which is why it is not DEBUG-only ──────────


def test_the_first_refusal_says_so_at_info(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The three INFO lines that used to mark this episode are gone with the
    re-logins that produced them. One line has to survive, or the next reporter
    has less in their log than @georghaberkorn68-ctrl had."""
    c = _portal_client()
    with caplog.at_level(logging.INFO, logger=_MODULE):
        asyncio.run(c._refresh_tokens(stale_access_token=_PORTAL_SENTINEL))

    records = [r for r in caplog.records if r.levelno == logging.INFO]
    assert records, "the refusal is invisible at INFO"
    text = records[0].getMessage()
    assert "read-only" in text and "data_act_portal" in text
    assert "Reads are unaffected" in text, (
        "the message must say what still works, or it reads as a breakage"
    )


def test_it_does_not_repeat_at_info_on_every_poll(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """#1866 is the precedent: the budget refusal used to log at ERROR on every
    attempt and read as a runaway loop. This fires on every native read of every
    poll, so the first one is news and the rest are DEBUG."""
    c = _portal_client()
    with caplog.at_level(logging.DEBUG, logger=_MODULE):
        async def _three() -> None:
            for _ in range(3):
                await c._refresh_tokens(stale_access_token=_PORTAL_SENTINEL)

        asyncio.run(_three())

    infos = [r for r in caplog.records if r.levelno == logging.INFO]
    debugs = [
        r for r in caplog.records
        if r.levelno == logging.DEBUG and "Refresh skipped" in r.getMessage()
    ]
    assert len(infos) == 1, f"the refusal shouted {len(infos)} times"
    assert len(debugs) == 2


def test_a_later_episode_is_news_again(monkeypatch) -> None:
    """The flag clears as soon as a refresh runs on a real token, so a car that
    recovers and then falls back again reports the second episode too."""
    c = _portal_client()
    asyncio.run(c._refresh_tokens(stale_access_token=_PORTAL_SENTINEL))
    assert c._cookie_session_refusal_reported is True

    # the native backend comes back: a real token, a real refresh
    c._tokens = TokenSet(
        access_token="STALE", refresh_token="RT", id_token="i",
        expires_at=0.0, strategy="mbb",
    )
    c._mbb_client_id = "CID"

    async def _fake(session, refresh_token, *, client_id):
        return _mbboauth.MbbTokenSet(
            access_token="NEW", refresh_token="RT",
            token_type="Bearer", expires_at=0.0,
        )

    monkeypatch.setattr(_mbboauth, "refresh", _fake)
    asyncio.run(c._refresh_tokens(stale_access_token="STALE"))

    assert c._cookie_session_refusal_reported is False
