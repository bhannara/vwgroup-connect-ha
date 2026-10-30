# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""#923 — three credential keys reached the diagnostics download unredacted,
and reading the redaction list was the reason nobody noticed.

The list in ``diagnostics.py`` is long, careful and annotated. Its own b11 note
says in so many words that *"the vw.de cookie list carries the auth0 / auth0-mf
SSO session tokens"* — and then registers the SUPPLEMENTARY slot's cookie jar
while leaving the PRIMARY one (``CONF_WEBSITE_COOKIES``) out. Both sibling jars
were covered, so the gap read as closed to anyone checking the list against
itself. The same shape had happened to two token maps: Companion, VW-EU two-way
and Škoda were registered, ``CONF_MBB_COMMAND_TOKENS`` and
``CONF_SUPPLEMENTARY_TIBBER_TOKENS`` were not.

All three live in ``entry.data``, which ``async_get_config_entry_diagnostics``
emits as ``config``. A cookie or token value is an opaque string, so none of the
generic branches — which match e-mail, VIN, coordinate and base64 shapes — would
mask one. The download is the file this project asks users to attach to public
issues, and two were attached to #923 on the day this was found.

So this file does not check the list against itself. It derives what *ought* to
be redacted from the names in ``const.py`` and fails when a key is added there
without being handled here. That is the project's own rule: the completeness of
a guard is itself a test, not a careful reading.
"""
from __future__ import annotations

import re

import pytest

from custom_components.vag_connect import const, diagnostics

# A config key whose NAME says it carries a credential. Deliberately a name
# test: a new key is added to const.py long before anyone thinks about this
# file, and the name is the only thing available at that moment.
#
# Unanchored on purpose. The first version of this pattern anchored the words
# at the end of the name and so missed CONF_WEBSITE_COOKIES — plural — which is
# one of the three keys this file exists for. The positive control below caught
# that; the completeness assertion would have passed either way, because the
# keys were already in the list by then. An instrument that silently matches
# nothing is the failure this whole file is about.
_SECRET_NAME = re.compile(
    r"COOKIE|TOKEN|PASSWORD|SECRET|SPIN|API_KEY|CREDENTIAL|_KEYS",
)

# Keys whose name matches but which are NOT credentials, each with the reason.
# Anything added here needs a reason that survives being read aloud.
_NOT_A_SECRET = {
    # A boolean opt-in ("store the password?"), not the password.
    "CONF_VWEU_TWOWAY_STORE_PASSWORD",
}

# Keys handled by a dedicated masker rather than by wholesale redaction,
# because the shape carries triage value (a count, an expiry) that is worth
# keeping once the secret inside it is masked.
_HANDLED_ELSEWHERE = {
    # {VIN: {key, id, validUntil}} — routed through _redact_identifier_map so
    # the enrolment count survives while each record is masked.
    "CONF_SKODA_OFFICIAL_KEYS": "_redact_identifier_map",
}


def _secret_conf_keys() -> dict[str, str]:
    """{const name: its string value} for every credential-shaped key."""
    return {
        name: getattr(const, name)
        for name in dir(const)
        if name.startswith("CONF_")
        and isinstance(getattr(const, name), str)
        and _SECRET_NAME.search(name)
        and name not in _NOT_A_SECRET
    }


def test_the_name_filter_finds_the_keys_it_is_supposed_to() -> None:
    """Positive control. A completeness test whose filter matches nothing would
    pass for ever and guard nothing."""
    found = _secret_conf_keys()
    for expected in (
        "CONF_PASSWORD",
        "CONF_SPIN",
        "CONF_WEBSITE_COOKIES",
        "CONF_MBB_COMMAND_TOKENS",
        "CONF_SUPPLEMENTARY_TIBBER_TOKENS",
        "CONF_VWEU_TWOWAY_COOKIES",
        "CONF_COMPANION_AGENT_TOKEN",
        "CONF_ABRP_USER_TOKEN",
    ):
        assert expected in found, f"the filter no longer finds {expected}"
    assert "CONF_VWEU_TWOWAY_STORE_PASSWORD" not in found
    assert len(found) >= 15, f"only {len(found)} credential keys found"


def test_every_credential_key_is_redacted_or_explicitly_handled() -> None:
    """The guard itself: a new credential key in const.py must be handled."""
    unhandled = sorted(
        name
        for name, value in _secret_conf_keys().items()
        if value not in diagnostics._REDACT_KEYS
        and name not in _HANDLED_ELSEWHERE
    )
    assert not unhandled, (
        "these credential keys reach the diagnostics download unredacted:\n  "
        + "\n  ".join(unhandled)
        + "\n\nAdd each to _REDACT_KEYS in diagnostics.py, or to "
        "_HANDLED_ELSEWHERE here with the masker that covers it and why."
    )


@pytest.mark.parametrize(
    "key",
    [
        const.CONF_WEBSITE_COOKIES,
        const.CONF_MBB_COMMAND_TOKENS,
        const.CONF_SUPPLEMENTARY_TIBBER_TOKENS,
    ],
)
def test_the_three_found_keys_really_are_masked_now(key: str) -> None:
    """Membership in a set is not the behaviour. These three go through the
    scrubber in the shape they are actually stored in."""
    stored = {
        const.CONF_WEBSITE_COOKIES: [
            {"name": "auth0", "value": "s3ss10n-c00k13-value", "domain": ".volkswagen.de"},
        ],
        const.CONF_MBB_COMMAND_TOKENS: {"WVWZZZAUZFW000000": {"access": "tok-abc"}},
        const.CONF_SUPPLEMENTARY_TIBBER_TOKENS: {"access_token": "tib-xyz"},
    }[key]

    out = diagnostics._scrub({key: stored})
    assert out[key] == "**REDACTED**", f"{key} survived the scrubber as {out[key]!r}"

    # And the secret itself must not appear anywhere in the rendered output.
    rendered = repr(out)
    for secret in ("s3ss10n-c00k13-value", "tok-abc", "tib-xyz"):
        assert secret not in rendered


def test_a_cookie_jar_is_not_saved_by_the_generic_branches() -> None:
    """Why the omission mattered: nothing else would have caught it. Under a
    different key the same jar passes through untouched, which is exactly what
    happened while the key was missing from the list."""
    jar = [{"name": "auth0", "value": "s3ss10n-c00k13-value"}]
    out = diagnostics._scrub({"some_other_key": jar})
    assert "s3ss10n-c00k13-value" in repr(out), (
        "a generic branch now masks opaque token values; if that is deliberate "
        "this test should be replaced, but the key list is still the guard"
    )
