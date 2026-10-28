# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""#1947 — the portal put both credentials on one page and we stopped reading.

On 2026-10-26 the EU Data Act portal replaced its two-step sign-in with a page
that asks for the identifier and the password together. The old code required
the token that binds step one to step two; a one-page form has no second step,
so that token is simply absent, and its absence was read as "we cannot
understand this page". The password was never sent.

Twelve reporters across SEAT and CUPRA, in Germany, the Netherlands and
Finland, within two days — and because the other sign-in route is refused for
those brands at the same moment, **both** paths ended in failure and the repair
dialog told every one of them their e-mail or password was wrong. Three of them
said they had re-checked their credentials because of it. That sentence was the
worst part of the incident, and it is why the detection below keys on a shape
it can recognise rather than on the absence of something it expected.

The field list in the old error message is what made this diagnosable from the
outside: reporters quoted `['password', 'state', 'username']` and the shape was
obvious before anyone had read the code. That list is deliberately kept.

The fixtures are built from the field names the reporters actually quoted and
from our own debug log of the classic flow, not invented.
"""
from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock

import pytest

from custom_components.vag_connect.cariad.auth._eu_data_act import (
    EUDataActConnector,
    _login_fields,
    _single_page_login_keys,
)
from custom_components.vag_connect.cariad.exceptions import AuthenticationError

_EMAIL = "owner@example.invalid"
_PASSWORD = "correct horse"

# The new page, as the reporters' error quoted it: password, state, username.
_ONE_PAGE_HTML = (
    '<form action="/login/authenticate" method="post">'
    '<input type="hidden" name="state" value="ST4TE">'
    '<input type="text" name="username" value="">'
    '<input type="password" name="password" value="">'
    '<button type="submit">Sign in</button>'
    "</form>"
)

# The classic first page, as our own debug log records its fields:
# step1 fields=['_csrf', 'relayState', 'hmac'].
_TWO_STEP_HTML = (
    '<script>window._IDK = {templateModel: {"hmac":"HM4C","relayState":"RS"},'
    ' csrf_token: "CSRF1"};</script>'
    '<form action="login/identifier" method="post">'
    '<input type="hidden" name="_csrf" value="CSRF1">'
    "</form>"
)
_TWO_STEP_PASSWORD_HTML = (
    '<script>window._IDK = {templateModel: {"hmac":"FRESH","relayState":"RS"},'
    ' csrf_token: "CSRF2"};</script>'
    '<form action="login/authenticate" method="post">'
    '<input type="hidden" name="_csrf" value="CSRF2">'
    "</form>"
)

# Neither shape: no password input anywhere.
_UNREADABLE_HTML = (
    '<form action="/x"><input type="hidden" name="state" value="S"></form>'
)
# A password field but nothing to put an identifier in. Must NOT be guessed at.
_PASSWORD_ONLY_HTML = (
    '<form action="/x">'
    '<input type="hidden" name="state" value="S">'
    '<input type="password" name="password" value="">'
    "</form>"
)

_LANDING = "https://portal.invalid/dashboard"


# ── the discriminator, on its own ──────────────────────────────────────────


def test_the_reported_page_is_recognised_as_one_page() -> None:
    """The exact field set the reporters quoted."""
    fields, _ = _login_fields(_ONE_PAGE_HTML)
    assert sorted(fields) == ["password", "state", "username"], sorted(fields)
    assert _single_page_login_keys(fields) == ("username", "password")


def test_the_classic_first_page_is_not_mistaken_for_one() -> None:
    """It has no password input, so it cannot be a one-page form however the
    binding token behaves. Asserted because misreading this direction would
    post a password into the identifier step."""
    fields, _ = _login_fields(_TWO_STEP_HTML)
    assert "hmac" in fields
    assert _single_page_login_keys(fields) is None


@pytest.mark.parametrize(
    "html", [_UNREADABLE_HTML, _PASSWORD_ONLY_HTML],
    ids=["no-password-input", "password-but-no-identifier"],
)
def test_an_unrecognised_page_is_not_guessed_at(html: str) -> None:
    """The detection answers "yes, this shape" or nothing at all.

    The second case is the one that matters: a page carrying a password input
    and no identifier is not a one-page form, and posting credentials to it on
    the strength of the password field alone would be sending a password
    somewhere on a guess.
    """
    fields, _ = _login_fields(html)
    assert _single_page_login_keys(fields) is None


def test_a_classic_page_with_a_prefilled_email_is_not_one_page() -> None:
    """The dangerous near-miss, and a mutation check had to find it.

    ``_login_fields`` lifts a prefilled address out of the page's own state
    model, so a classic FIRST page can carry an ``email`` field while still
    asking only for the identifier. Recognising a one-page form by its
    identifier alone would post the password to a page that never asked for
    one. The password input is what makes a one-page form, and this is the
    fixture that proves that half of the test is load-bearing.
    """
    html = (
        '<script>window._IDK = {templateModel: {"hmac":"HM4C",'
        '"relayState":"RS","emailPasswordForm":{"email":"owner@example.invalid"}},'
        ' csrf_token: "CSRF1"};</script>'
        '<form action="login/identifier" method="post">'
        '<input type="hidden" name="_csrf" value="CSRF1">'
        "</form>"
    )
    fields, _ = _login_fields(html)
    assert "email" in fields, "fixture is wrong: the prefill did not land"
    assert "password" not in fields
    assert _single_page_login_keys(fields) is None, (
        "a page that only asks for the identifier was taken for a one-page "
        "form, so the password would be posted to the identifier step"
    )


def test_the_two_step_shape_wins_when_a_page_looks_like_both() -> None:
    """Precedence, pinned rather than left to the order of two conditions.

    If a page ever carries the step-binding token AND both inputs, the classic
    flow is the one to trust: it is the one we have measured end to end. The
    one-page path is only consulted when that token is absent.
    """
    html = (
        '<script>window._IDK = {templateModel: {"hmac":"HM4C","relayState":"RS"},'
        ' csrf_token: "CSRF1"};</script>'
        '<form action="login/identifier" method="post">'
        '<input type="hidden" name="_csrf" value="CSRF1">'
        '<input type="text" name="username" value="">'
        '<input type="password" name="password" value="">'
        "</form>"
    )
    conn, seen = _connector(html, _TWO_STEP_PASSWORD_HTML)
    _login(conn)

    assert len(seen["posts"]) == 1, (
        "the one-page path was taken for a page that still binds two steps"
    )
    # The page's own empty password input is echoed back, exactly as a browser
    # would. What must not travel is the VALUE.
    assert seen["posts"][0]["data"].get("password") != _PASSWORD, (
        "the password was sent to the identifier step"
    )


@pytest.mark.parametrize(
    "identifier", ["username", "email", "identifier", "user", "userId"]
)
def test_the_identifier_field_may_be_named_several_ways(identifier: str) -> None:
    """Only `username` is measured; the rest are accepted because a one-page
    form is recognised by its SHAPE, and pinning the shape to one spelling
    would re-break on a rename that changes nothing else."""
    html = (
        f'<form action="/a"><input name="{identifier}" value="">'
        '<input type="password" name="password" value=""></form>'
    )
    fields, _ = _login_fields(html)
    assert _single_page_login_keys(fields) == (identifier, "password")


# ── end to end through the login worker ────────────────────────────────────


def _connector(signin_html: str, password_page_html: str = "") -> tuple[Any, dict]:
    """A connector whose sign-in page is *signin_html*.

    ``_follow_login_redirects`` is replaced so the test observes the POST this
    change decides to make, rather than simulating the portal's whole redirect
    chain — the chain is not what moved.
    """
    seen: dict[str, Any] = {"follow": [], "posts": []}

    class _Resp:
        def __init__(self, url: str, html: str) -> None:
            self.url = url
            self._html = html

        async def __aenter__(self) -> "_Resp":
            return self

        async def __aexit__(self, *_a: Any) -> bool:
            return False

        async def text(self, errors: str | None = None) -> str:
            return self._html

    class _Session:
        closed = False

        def get(self, url: str, **kw: Any) -> Any:
            return _Resp("https://identity.invalid/signin", signin_html)

        def post(self, url: str, **kw: Any) -> Any:
            seen["posts"].append({"url": url, "data": dict(kw.get("data") or {})})
            return _Resp(
                "https://identity.invalid/authenticate", password_page_html
            )

    conn = EUDataActConnector(_Session(), brand="cupra")  # type: ignore[arg-type]

    async def _follow(method: str, url: str, **kw: Any) -> tuple[str, str, int]:
        seen["follow"].append(
            {"method": method, "url": url, "data": dict(kw.get("data") or {})}
        )
        return _LANDING, "<html>ok</html>", 200

    conn._follow_login_redirects = _follow  # type: ignore[method-assign]
    # The landing checks after the credential POST are not what moved here.
    conn._is_consent_landing = lambda *_a: False  # type: ignore[method-assign]
    conn._is_terms_landing = lambda *_a: False  # type: ignore[method-assign]
    conn._skip_marketing_consent_landing = AsyncMock(return_value=None)  # type: ignore[method-assign]
    return conn, seen


def _login(conn: Any) -> BaseException | None:
    try:
        asyncio.run(conn._login_impl(_EMAIL, _PASSWORD))
    except BaseException as err:  # noqa: BLE001 - the shape is asserted by caller
        return err
    return None


def test_the_one_page_form_sends_both_credentials_in_one_post() -> None:
    """The fix. One request, carrying both, and no identifier round-trip."""
    conn, seen = _connector(_ONE_PAGE_HTML)
    _login(conn)

    assert len(seen["follow"]) == 1, (
        f"expected one credential POST, got {len(seen['follow'])}"
    )
    body = seen["follow"][0]["data"]
    assert body["username"] == _EMAIL
    assert body["password"] == _PASSWORD
    assert body["state"] == "ST4TE", "the page's own hidden field must survive"
    assert seen["posts"] == [], (
        "an identifier step was sent to a page that asks for both at once"
    )


def test_the_classic_two_step_flow_is_unchanged() -> None:
    """THE counter-case. The old page must still take both steps in order, with
    the second page's fresh token, or this fix trades one broken brand for
    every other."""
    conn, seen = _connector(_TWO_STEP_HTML, _TWO_STEP_PASSWORD_HTML)
    _login(conn)

    assert len(seen["posts"]) == 1, "the identifier step did not happen"
    assert seen["posts"][0]["data"]["email"] == _EMAIL
    assert seen["posts"][0]["data"]["hmac"] == "HM4C"
    assert "password" not in seen["posts"][0]["data"], (
        "the password was sent to the identifier step"
    )

    assert len(seen["follow"]) == 1
    body = seen["follow"][0]["data"]
    assert body["password"] == _PASSWORD
    assert body["email"] == _EMAIL
    assert body["hmac"] == "FRESH", (
        "the credential POST must carry the SECOND page's token, not the first"
    )


def test_an_unreadable_page_still_fails_loudly_with_its_fields() -> None:
    """A page that is neither shape must not be posted a password, and the
    error must keep naming the fields — that list is how #1947 was diagnosed
    from the outside before anyone read the code."""
    conn, seen = _connector(_UNREADABLE_HTML)
    err = _login(conn)

    assert isinstance(err, AuthenticationError)
    assert "could not parse the sign-in form" in str(err)
    assert "state" in str(err), "the field list is gone from the message"
    assert seen["follow"] == [] and seen["posts"] == [], (
        "credentials were sent to a page we could not read"
    )


def test_a_password_field_alone_is_not_enough_to_post_to() -> None:
    """The guess the detection refuses to make."""
    conn, seen = _connector(_PASSWORD_ONLY_HTML)
    err = _login(conn)

    assert isinstance(err, AuthenticationError)
    assert seen["follow"] == [] and seen["posts"] == []
