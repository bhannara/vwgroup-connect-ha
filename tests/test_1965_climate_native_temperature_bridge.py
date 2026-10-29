# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""#1965 — what HA 2026.11 changes for us, and the date the bridge expires.

The scheduled beta watch found three failures against 2026.11.0b0, and they are
three different kinds of thing:

1. **A real API change.** ``ClimateEntity`` got the native-unit treatment that
   sensors have had for years: ``temperature_unit``, ``current_temperature``
   and ``target_temperature`` — and their ``_attr_`` twins — became
   ``Final = DeprecatedEntityProperty``, replaced by ``native_*`` names, with
   removal announced for 2027.11. Assigning or overriding a ``Final`` is a
   mypy error, which is why it showed up as a type failure rather than a test
   failure.

2. **A dependency that stopped being present.** ``httpx`` is not part of Home
   Assistant's dependency set. On an environment without it,
   ``--ignore-missing-imports`` turns ``httpx.Response`` into ``Any`` and
   ``--warn-return-any`` rejects three returns in ``_http2.py`` that are
   plainly strings. Annotating the locals states the fact instead of hiding it.

3. **A cosmetic upstream change that a test turned into a breakage.** HA
   flipped ``SSL_ALPN_HTTP11_HTTP2`` from ``("http/1.1", "h2")`` to
   ``("h2", "http/1.1")``. We pass that constant through untouched and never
   read its order, so nothing about our behaviour changed — only an assertion
   that had pinned a neighbour's preference.

Only the first one is a decision. We keep the deprecated climate members
because the native names **do not exist before 2026.11** (measured absent on
2026.10.1) and ``hacs.json`` declares a floor of 2026.6.0, so migrating now
would break the climate entity for everyone who has not updated. For a custom
integration the deprecation only logs a warning — the ``RuntimeError`` path in
``migrate_deprecated_entity_members`` is reachable only for modules under
``homeassistant.components.`` — so the bridge is safe, not merely convenient.

What makes it a bridge rather than a shrug is the gate below: the moment the
declared floor reaches 2026.11, the deprecated members have to be gone.
"""
from __future__ import annotations

import json
import pathlib

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_CLIMATE = _ROOT / "custom_components/vag_connect/climate.py"
_HTTP2 = _ROOT / "custom_components/vag_connect/cariad/auth/_http2.py"
_FLOOR_TEST = _ROOT / "tests/test_1858_repairs_import_floor.py"

_DEPRECATED = ("_attr_temperature_unit", "current_temperature", "target_temperature")
_NATIVE = (
    "_attr_native_temperature_unit",
    "native_current_temperature",
    "native_target_temperature",
)


def _declared_floor() -> tuple[int, int]:
    cfg = json.loads((_ROOT / "hacs.json").read_text(encoding="utf-8"))
    major, minor = (int(p) for p in cfg["homeassistant"].split(".")[:2])
    return major, minor


# ── the decision, written where it is taken ────────────────────────────────


def test_the_bridge_names_its_own_expiry() -> None:
    """A deadline that lives only in a chat log is not a deadline.

    The removal version has to be in the file that carries the debt, so the
    next person reading ``climate.py`` learns it there rather than from an
    issue they would have to know to look for.
    """
    src = _CLIMATE.read_text(encoding="utf-8")
    assert "2027.11" in src, (
        "the climate bridge no longer states when the deprecated members are "
        "removed; #1965 put that date in the class body on purpose"
    )
    assert "#1965" in src
    for native in _NATIVE:
        assert native in src, (
            f"the note no longer names {native}, so the migration target is "
            f"not discoverable from the code that needs it"
        )


def test_the_ignores_are_narrow() -> None:
    """A bare ``# type: ignore`` would also hide the next, unrelated error."""
    bare = [
        f"{i}: {line.strip()}"
        for i, line in enumerate(_CLIMATE.read_text(encoding="utf-8").splitlines(), 1)
        if "type: ignore" in line and "type: ignore[" not in line
    ]
    assert bare == [], f"blanket type-ignores in climate.py: {bare}"


def test_every_deprecated_member_is_actually_silenced() -> None:
    """All three, or CI goes red on 2026.11 for the one that was missed."""
    lines = _CLIMATE.read_text(encoding="utf-8").splitlines()
    assert any(
        "_attr_temperature_unit" in ln and "type: ignore[misc]" in ln for ln in lines
    ), "the unit assignment is not silenced"
    for i, ln in enumerate(lines):
        for member in ("def current_temperature", "def target_temperature"):
            if ln.strip().startswith(member):
                decorator = lines[i - 1]
                assert "type: ignore[misc]" in decorator, (
                    f"{member} overrides a Final attribute on 2026.11 and its "
                    f"decorator line carries no ignore: {decorator.strip()!r}"
                )


# ── the gate that ends the bridge ──────────────────────────────────────────


def test_the_bridge_ends_when_the_floor_reaches_2026_11() -> None:
    """Dormant today, and the only reason this file is worth having.

    Raising the floor in ``hacs.json`` is the moment the deprecated members
    stop being a compatibility measure and start being debt. This fails then,
    and names the three replacements so the change is mechanical.
    """
    floor = _declared_floor()
    if floor < (2026, 11):
        pytest.skip(
            f"floor is {floor[0]}.{floor[1]}; the deprecated climate members "
            f"are still the only ones that exist on it"
        )
    src = _CLIMATE.read_text(encoding="utf-8")
    still_there = [m for m in _DEPRECATED if f"def {m}" in src or f"{m} =" in src]
    assert still_there == [], (
        f"hacs.json now floors at {floor[0]}.{floor[1]}, so the native climate "
        f"API exists everywhere this runs. Replace {still_there} with "
        f"{list(_NATIVE)} and drop the three type-ignores."
    )


# ── the other two, pinned so they cannot quietly come back ─────────────────


def test_the_http2_text_returns_are_typed() -> None:
    """``--warn-return-any`` only bites where httpx is absent, which is every
    environment that does not install it for us. A bare return would pass here
    and fail there, so the shape is pinned rather than the mypy run."""
    src = _HTTP2.read_text(encoding="utf-8")
    body = src.split("async def text(", 1)[1].split("async def json(", 1)[0]
    offenders = [
        ln.strip()
        for ln in body.splitlines()
        if ln.strip().startswith("return self._resp")
    ]
    assert offenders == [], (
        f"these return an untyped expression from a function declared -> str, "
        f"which fails mypy wherever httpx is not installed: {offenders}"
    )


def test_the_alpn_bucket_is_not_pinned_by_order() -> None:
    """We hand the constant to ``client_context`` and never read its order.
    Asserting the order made HA 2026.11's protocol-preference change look like
    a breakage in this integration."""
    src = _FLOOR_TEST.read_text(encoding="utf-8")
    assert 'SSL_ALPN_HTTP11_HTTP2 == ("http/1.1", "h2")' not in src, (
        "the ALPN assertion pins Home Assistant's protocol preference again; "
        "compare the contents, not the order"
    )
    assert "set(SSL_ALPN_HTTP11_HTTP2)" in src


def test_we_do_not_read_the_alpn_order_anywhere() -> None:
    """The claim the test above rests on, measured rather than asserted."""
    import re

    hits: list[str] = []
    for path in (_ROOT / "custom_components").rglob("*.py"):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "SSL_ALPN_HTTP11_HTTP2" not in line:
                continue
            # An import or a bare pass-through is fine; indexing or unpacking
            # it would mean we depend on which protocol comes first.
            if re.search(r"SSL_ALPN_HTTP11_HTTP2\s*\[", line):
                hits.append(f"{path.name}:{i}: {line.strip()}")
    assert hits == [], f"something now depends on the ALPN order: {hits}"
