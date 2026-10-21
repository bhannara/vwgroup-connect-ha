# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""A reading that never arrived, reported as a definite "offline".

@Mex-ai11's Audi A6 (#1851) reported `connection state: online` and
`vehicle status: OFFLINE` at the same moment, on an entry whose feed had been
frozen since 12 October. The OFFLINE was not a measurement. It was manufactured
from a field that did not come.

``v()`` returns ``None`` when a path is absent, and the Volkswagen EU
connector — which serves Audi too — wrote ``… is True``, so ``None`` collapsed
to ``False``. On a feed that has stopped, the readiness field stops arriving
with everything else, so the integration confidently reported the car offline
while the official app showed it online. That contradiction is what sent him
to re-authenticate and rebuild his entry, twice, for nothing.

The contract is written into the dataclass itself (``cariad/models.py``):

    # Parser miss must NOT default to "vehicle parked + offline".
    # Conditional automations like "wake car when leaving driveway" relied
    # on ``is_online`` being honest about its uncertainty.

``vw_na``, ``skoda`` and ``seat_cupra`` all check the type before assigning.
This one did not — and ``tests/test_cariad.py`` asserted the wrong behaviour,
holding it in place.

**Downstream was already right**, which is what makes the fix safe rather than
a ripple: ``coordinator.py`` treats the field as tri-state and reads only an
explicit ``False`` as OFFLINE (#923). The connector was the only liar.
"""
from __future__ import annotations

import ast
import inspect
import pathlib

import pytest

from custom_components.vag_connect.cariad import models


def _vw_eu_source() -> str:
    from custom_components.vag_connect.cariad.api import vw_eu

    return inspect.getsource(vw_eu)


# ── the contract ───────────────────────────────────────────────────────────


def test_the_field_is_allowed_to_be_unknown() -> None:
    """If this ever becomes a plain ``bool`` the whole question changes, and
    the fix below would be silently undone by the type."""
    hints = models.VehicleData.__annotations__
    assert "None" in str(hints["is_online"]), (
        f"is_online is no longer tri-state: {hints['is_online']}"
    )
    assert models.VehicleData(vin="WVWZZZAUZFW000000").is_online is None, "the default is no longer unknown"


def test_the_contract_is_still_written_down() -> None:
    """The comment is the reason the other connectors guard. If it goes, the
    next person has only four implementations and no statement of intent.

    Scoped to the comment block above this field. The first version asserted
    the sentence appeared anywhere in ``models.py``, and the phrase "must NOT
    default to" occurs three times in that file — for charging and for climate
    as well — so deleting the one that governs ``is_online`` left the test
    passing on the other two. The mutation check is what said so.
    """
    src = inspect.getsource(models)
    field = src.index("is_online: bool | None")
    window = src[max(0, field - 420):field]
    assert "must NOT default to" in window, (
        "the comment above is_online no longer states that a parser miss must "
        "not default to offline; that sentence is why three connectors check "
        f"first. Window was: {window[-300:]!r}"
    )
    assert "vehicle parked + offline" in window


# ── the fix, where it was wrong ────────────────────────────────────────────


def test_a_missing_readiness_reading_stays_unknown() -> None:
    """The reported case, driven through the real parser."""
    from custom_components.vag_connect.cariad.api import vw_eu

    client = vw_eu.VWEUClient.__new__(vw_eu.VWEUClient)
    result = client._parse_status("WVWZZZAUZFW000000", {}, {})
    assert result.is_online is None, (
        "a payload with no readiness path still reports a definite offline"
    )


@pytest.mark.parametrize("value", [True, False])
def test_a_reading_that_did_arrive_is_still_honoured(value: bool) -> None:
    """The guard must not throw away the answer when there is one — including
    an explicit False, which is a real offline and must survive."""
    from custom_components.vag_connect.cariad.api import vw_eu

    client = vw_eu.VWEUClient.__new__(vw_eu.VWEUClient)
    # The full six-segment path. ``_val(d, 'a', 'b', 'c')`` walks
    # ``d['a']['b']['c']`` (base.py), so a fixture that skips a level reads as
    # "absent" and would make this test pass for the wrong reason — the first
    # version of it did exactly that and said so, which is why the parser is
    # driven here rather than the assignment being asserted from source alone.
    payload = {
        "readiness": {
            "readinessStatus": {
                "value": {"connectionState": {"isOnline": value}}
            }
        }
    }
    result = client._parse_status("WVWZZZAUZFW000000", payload, {})
    assert result.is_online is value


def test_the_assignment_is_type_checked_rather_than_identity_checked() -> None:
    """Pinned at the source as well as through behaviour.

    A fixture can only prove the shapes it happens to feed. ``… is True`` is a
    one-character-class mistake that any future edit could reintroduce while
    every behavioural test above still passed on the shapes it knows.
    """
    tree = ast.parse(_vw_eu_source())
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        targets = [ast.unparse(t) for t in node.targets]
        if not any(t.endswith(".is_online") for t in targets):
            continue
        rendered = ast.unparse(node.value)
        if rendered.endswith("is True") or rendered.endswith("is not None"):
            offenders.append(rendered)
    assert not offenders, (
        f"is_online is assigned from a truthiness/identity test again: {offenders}"
    )


# ── the other three, so this stays a fixed inconsistency ───────────────────


def _is_online_is_guarded(source: str) -> tuple[bool, str]:
    """Is every assignment to ``.is_online`` protected from an absent value?

    Read from the syntax tree, not from a window of characters around the
    assignment. The first version of this searched 600 characters either side
    for the word ``isinstance``, and unrelated code in that neighbourhood
    satisfied it — removing Škoda's real guard left the test passing. Proximity
    is not containment.

    Two shapes count, which are the two the codebase actually uses:

    * the assignment sits inside an ``if`` whose test calls ``isinstance``;
    * the assigned expression itself compares against ``None`` (Škoda's
      ``unreachable is None or unreachable is False``).
    """
    tree = ast.parse(source)

    # Parent links, so an assignment can be asked what encloses it.
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node

    def enclosing_isinstance_subjects(node: ast.AST) -> set[str]:
        """Every name an enclosing ``if isinstance(name, …)`` has type-checked.

        The subject matters, not the presence of the word. The second version
        of this accepted ANY enclosing isinstance, and Škoda's assignment sits
        inside ``if isinstance(readiness, dict)`` — a type check on a different
        object entirely — so removing its real guard still passed. Proximity is
        not containment, and containment is not protection of *this* value.
        """
        subjects: set[str] = set()
        cur: ast.AST | None = node
        while cur is not None:
            parent = parents.get(cur)
            if isinstance(parent, ast.If) and cur in parent.body:
                for call in ast.walk(parent.test):
                    if (
                        isinstance(call, ast.Call)
                        and isinstance(call.func, ast.Name)
                        and call.func.id == "isinstance"
                        and call.args
                        and isinstance(call.args[0], ast.Name)
                    ):
                        subjects.add(call.args[0].id)
            cur = parent
        return subjects

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(ast.unparse(t).endswith(".is_online") for t in node.targets):
            continue
        rendered = ast.unparse(node.value)
        if "is None" in rendered:
            return True, f"guarded in the expression: {rendered}"
        used = {n.id for n in ast.walk(node.value) if isinstance(n, ast.Name)}
        checked = enclosing_isinstance_subjects(node) & used
        if checked:
            return True, f"guarded by isinstance on {sorted(checked)}: {rendered}"
        return False, f"unguarded assignment: {rendered}"
    return False, "no assignment to is_online found at all"


@pytest.mark.parametrize("module_name", ["vw_eu", "vw_na", "skoda", "seat_cupra"])
def test_every_connector_guards_the_assignment(module_name: str) -> None:
    """Including the one this issue fixed, so it cannot quietly regress, and
    so a later "cleanup" that unifies the four on the *wrong* implementation
    fails loudly."""
    import custom_components.vag_connect.cariad.api as api_pkg

    path = pathlib.Path(api_pkg.__file__).parent / f"{module_name}.py"
    guarded, why = _is_online_is_guarded(path.read_text(encoding="utf-8"))
    assert guarded, (
        f"{module_name} would now report a missing readiness reading as a "
        f"definite offline — {why}"
    )


def test_every_connector_is_covered_by_this_check() -> None:
    """The completeness half.

    Naming three modules is only worth something if three is all there are. A
    fifth brand connector added later would otherwise inherit the defect and
    no test would mention it.
    """
    import custom_components.vag_connect.cariad.api as api_pkg

    api_dir = pathlib.Path(api_pkg.__file__).parent
    writers = [
        path.stem
        for path in sorted(api_dir.glob("*.py"))
        if ".is_online =" in path.read_text(encoding="utf-8")
    ]
    assert set(writers) == {"vw_eu", "vw_na", "skoda", "seat_cupra"}, (
        f"the set of connectors writing is_online changed: {writers}. A new one "
        "must either guard the assignment or be added to the test above."
    )
