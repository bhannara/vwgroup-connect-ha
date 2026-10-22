# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""A calendar that dropped every value it was given.

@nijaobscvra666 (#1923) reported an empty service calendar on a CUPRA Leon and
did not stop at the symptom: he found the cause at the line. ``_parse_date``
required a ``str`` and returned ``None`` for anything else, and **no writer in
the integration ever produces a string** for the two service fields.
``service_due_at`` and ``oil_service_at`` are integer day counts from every one
of them — ``seat_cupra``, ``skoda``, ``vw_eu`` and the EU Data Act parser —
because that is what the backends send and what the day-counter sensors read.

So *Service due* and *Oil service due* had never rendered, on any brand, on
either channel, for as long as the platform has existed. Two of the nine events
on that entity; the other seven survived because their writers already convert
at the source.

It presented as an empty calendar rather than a missing one, which is the part
that makes it hard to notice: the setup gate only asks whether a service field
is truthy, and a day count is, so the entity is created and then every event in
it is dropped.

**Why it reached a reporter instead of CI**: the test that covers this fed
``"2026-12-01"`` — a shape nothing produces. It was green, had always been
green, and asserted a case that cannot occur. That test now drives day counts;
these pin the rest.

**The anchor is deliberate.** ``dt_util.now().date()`` is what ``_all_events``
already uses for "today". Three implementations of this conversion exist in the
repository and all three anchor differently — ``cariad/_util.py`` on UTC
midnight, ``sensor.py`` on ``date.today()`` (the system zone, not Home
Assistant's configured one), and the calendar on ``dt_util``. They disagree by
up to a day near midnight. Aligning them is a separate change; the calendar
agreeing with itself is this one.
"""
from __future__ import annotations

import ast
import inspect
import pathlib
from datetime import date, datetime, timedelta, timezone

import pytest
from homeassistant.util import dt as dt_util

from custom_components.vag_connect.calendar import _parse_date


# ── the reported case ──────────────────────────────────────────────────────


def test_an_integer_day_count_becomes_a_date() -> None:
    """The fix, at the value the writers actually hand over."""
    assert _parse_date(180) == dt_util.now().date() + timedelta(days=180)
    assert _parse_date(0) == dt_util.now().date()


def test_an_overdue_service_is_a_date_in_the_past() -> None:
    """Negative counts are real: a service that is overdue reports how long
    ago it was due, and clamping that to today would hide it."""
    assert _parse_date(-12) == dt_util.now().date() - timedelta(days=12)


def test_the_anchor_matches_the_rest_of_the_module() -> None:
    """Pinned because it is the one decision in this fix that could be made
    three different defensible ways, and the wrong one is invisible except for
    a few minutes around midnight.

    Read from the syntax tree with the docstring removed. The first version
    asserted ``"date.today()" not in src`` over the raw source and failed
    immediately — on the docstring above, which names ``date.today()`` while
    explaining why it is *not* used. A text gate cannot tell an implementation
    from the prose describing it.
    """
    import textwrap

    tree = ast.parse(textwrap.dedent(inspect.getsource(_parse_date)))
    func = tree.body[0]
    assert isinstance(func, ast.FunctionDef)
    # Drop the docstring so only the implementation is judged.
    body = func.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]
    calls = {
        ast.unparse(node.func)
        for stmt in body
        for node in ast.walk(stmt)
        if isinstance(node, ast.Call)
    }
    assert "dt_util.now().date" in calls, (
        f"the day anchor no longer matches _all_events, so the calendar can "
        f"disagree with itself by a day near midnight. Calls found: {sorted(calls)}"
    )
    assert "date.today" not in calls, (
        "date.today() is the system zone, not Home Assistant's configured one"
    )
    assert "datetime.now" not in calls, (
        "a UTC anchor would disagree with _all_events in the same file"
    )


# ── the shapes it must still handle ────────────────────────────────────────


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-09-01", date(2026, 9, 1)),
        ("2026-09-01T00:00:00Z", date(2026, 9, 1)),
        (date(2026, 9, 1), date(2026, 9, 1)),
        (datetime(2026, 9, 1, 13, 30, tzinfo=timezone.utc), date(2026, 9, 1)),
    ],
)
def test_the_other_shapes_still_parse(value: object, expected: date) -> None:
    """Fixing the new shape must not drop the old one. The field is typed
    ``Any`` and a future parser may well hand over an ISO date."""
    assert _parse_date(value) == expected


@pytest.mark.parametrize("value", [None, "bad", "", "2026-09", [], {}, object()])
def test_rubbish_is_still_rejected(value: object) -> None:
    assert _parse_date(value) is None


# ── the guards, each of which exists for a reason ──────────────────────────


@pytest.mark.parametrize("value", [True, False])
def test_a_bool_is_not_a_day_count(value: bool) -> None:
    """``bool`` is a subclass of ``int``. Without the guard, ``True`` would
    mean tomorrow and ``False`` would mean today — a confident wrong date from
    a field that was never a date."""
    assert _parse_date(value) is None


@pytest.mark.parametrize("value", [-2147483648, 2147483647, 36501, -36501])
def test_a_sentinel_integer_is_not_a_date(value: int) -> None:
    """Backends ship sentinels such as -2147483648 inside error envelopes. A
    calendar entry 5.8 million years out is a parse failure wearing a date."""
    assert _parse_date(value) is None


@pytest.mark.parametrize("value", [36500, -36500])
def test_the_bound_is_inclusive(value: int) -> None:
    """The edge belongs to the accepted side, so a century-out value is kept
    rather than being lost to an off-by-one in the guard."""
    assert _parse_date(value) == dt_util.now().date() + timedelta(days=value)


# ── the premise, which is what actually broke ──────────────────────────────


def test_no_writer_produces_a_string_for_these_fields() -> None:
    """The fact the old implementation assumed away.

    If a writer ever does start producing an ISO string, that is fine — the
    string path still works. What must not happen quietly is the reverse: this
    test failing would mean the integer path has stopped being the live shape,
    and the comment explaining the fix would be describing history.
    """
    import custom_components.vag_connect as pkg

    root = pathlib.Path(pkg.__file__).parent
    writers: dict[str, list[str]] = {}
    for path in sorted(root.rglob("*.py")):
        if path.name == "calendar.py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:  # pragma: no cover - not expected in-tree
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                rendered = ast.unparse(target)
                if rendered.endswith((".service_due_at", ".oil_service_at")):
                    writers.setdefault(path.name, []).append(
                        ast.unparse(node.value)[:60]
                    )

    assert writers, (
        "no writer assigns service_due_at / oil_service_at any more; the "
        "integer day-count premise behind this fix needs re-checking"
    )
    # A literal ISO string would be the one shape that makes the old
    # implementation correct and this one unnecessary.
    for name, values in writers.items():
        for value in values:
            assert not value.startswith(('"20', "'20")), (
                f"{name} now writes a literal date string: {value}"
            )
