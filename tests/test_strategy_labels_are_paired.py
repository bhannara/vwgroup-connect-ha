# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""A gate compared a session label against a value nothing ever wrote.

``TokenSet.strategy`` says which sign-in produced a session, and a dozen places
branch on it. One of those comparisons named ``"hybrid_full"`` — and no sign-in
path in the shipping code has ever stamped that label. The hybrid flow takes
``hybrid_full`` as a keyword argument and stamps nothing, so its token set
carries the empty default. ``git log -S`` finds no commit that ever wrote it
under ``custom_components/``.

Two consumers were affected. One was a capability observation that quietly
reported one capability short. The other was a recovery watchdog built in
v2.8.0 for exactly the sessions that cannot renew themselves: it ran pre-flight
on every tick of the background poll loop, and its first check was that label.
It therefore returned immediately, for every entry, on every tick, for as long
as it existed. A whole recovery mechanism did nothing, and the only two
references to it in the suite replaced it with a stub, so nothing noticed.

**The missing test was a pairing test.** Both halves were individually
reasonable — something produces labels, something consumes them — and nothing
asserted that the two sets meet. That is the shape of the bug, not the specific
string, so this file pins the shape: every label the code compares against must
be one the code can produce. It is deliberately not a list of known-good
strings, because a list would have to be edited by the same person who forgot
to pair them.

The empty string is the legitimate exception: it is ``TokenSet.strategy``'s
default and means "a flow that stamps nothing", which is a real state several
sign-ins leave behind.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

_PKG = pathlib.Path(__file__).resolve().parents[1] / "custom_components/vag_connect"
_SOURCES = sorted(_PKG.rglob("*.py"))

# TokenSet.strategy's own default. A flow that stamps nothing leaves this, and
# code may legitimately compare against it.
_UNSTAMPED = ""


def _is_strategy_expr(node: ast.AST) -> bool:
    """True when *node* evaluates to a TokenSet's strategy label.

    Covers the three shapes the tree actually uses: a plain name bound from one
    (``strategy``), an attribute read (``tokens.strategy``), and the defensive
    ``getattr(tokens, "strategy", "")`` that most call sites prefer because the
    token set may be absent.
    """
    if isinstance(node, ast.Name):
        return node.id in {"strategy", "portal_strategy", "persisted_strategy"}
    if isinstance(node, ast.Attribute):
        return node.attr == "strategy"
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name) and func.id == "getattr" and len(node.args) >= 2:
            second = node.args[1]
            return isinstance(second, ast.Constant) and second.value == "strategy"
    return False


def _strings_in(node: ast.AST) -> set[str]:
    """Every string constant directly inside *node* (a value, tuple, set or list)."""
    out: set[str] = set()
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        out.add(node.value)
    elif isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        for elt in node.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                out.add(elt.value)
    return out


def _produced() -> dict[str, str]:
    """Labels a sign-in path can stamp, mapped to where it does so.

    Two shapes: the keyword on a ``TokenSet(...)`` construction, and a direct
    assignment onto an existing token set.
    """
    found: dict[str, str] = {}
    for path in _SOURCES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        rel = path.relative_to(_PKG.parent.parent).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg == "strategy":
                        for s in _strings_in(kw.value):
                            found.setdefault(s, f"{rel}:{kw.value.lineno}")
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute) and target.attr == "strategy":
                        for s in _strings_in(node.value):
                            found.setdefault(s, f"{rel}:{node.lineno}")
    return found


def _consumed() -> dict[str, str]:
    """Labels the code compares a strategy against, mapped to where."""
    found: dict[str, str] = {}
    for path in _SOURCES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        rel = path.relative_to(_PKG.parent.parent).as_posix()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            sides: list[ast.AST] = [node.left, *node.comparators]
            if not any(_is_strategy_expr(s) for s in sides):
                continue
            for side in sides:
                if _is_strategy_expr(side):
                    continue
                for s in _strings_in(side):
                    found.setdefault(s, f"{rel}:{node.lineno}")
    return found


# ── the measuring instruments, checked before they are trusted ─────────────


def test_the_scan_sees_the_whole_package() -> None:
    """A scan that found nothing would pass the pairing test vacuously."""
    assert len(_SOURCES) > 40, f"only {len(_SOURCES)} source files found"


def test_the_producer_scan_finds_the_known_stamps() -> None:
    """Grounded against labels that are definitely written somewhere. If this
    ever fails, the pairing test below has gone blind rather than green."""
    produced = _produced()
    for known in ("data_act_portal", "website_authproxy", "mbb", "device_grant"):
        assert known in produced, (
            f"the producer scan no longer sees {known!r}; it is written in the "
            f"tree, so the scan is broken, not the code. Found: {sorted(produced)}"
        )


def test_the_consumer_scan_finds_the_known_comparisons() -> None:
    """The same check for the other half."""
    consumed = _consumed()
    for known in ("mbb", "device_grant_portal"):
        assert known in consumed, (
            f"the consumer scan no longer sees {known!r} being compared "
            f"against; the scan is broken. Found: {sorted(consumed)}"
        )


# ── the pairing itself ─────────────────────────────────────────────────────


def test_every_consumed_strategy_label_can_actually_be_produced() -> None:
    """The test that was missing.

    A label the code branches on but never writes is a branch that cannot be
    taken. It does not fail loudly — it silently chooses the other path, which
    is why this survived in two places at once.
    """
    produced = _produced()
    consumed = _consumed()
    orphans = {
        label: where
        for label, where in consumed.items()
        if label != _UNSTAMPED and label not in produced
    }
    assert not orphans, (
        "these strategy labels are compared against but never written, so the "
        "comparison can only ever be False:\n"
        + "\n".join(f"  {label!r} at {where}" for label, where in sorted(orphans.items()))
        + "\n\nLabels the code can actually produce:\n"
        + "\n".join(f"  {label!r} at {where}" for label, where in sorted(produced.items()))
        + "\n\nEither stamp the label where the session is built, or stop "
        "comparing against it. Do not add it to an allow-list here."
    )


@pytest.mark.parametrize("dead", ["hybrid_full"])
def test_the_label_that_caused_this_is_gone(dead: str) -> None:
    """Named explicitly as well as caught generally.

    The general assertion above is the real guard, but this one names the value
    so that a reader who hits it learns the history instead of only the rule.
    ``hybrid_full`` remains a valid KEYWORD into the hybrid sign-in flow — what
    it is not, and never was, is a label on the resulting session.
    """
    assert dead not in _consumed(), (
        f"{dead!r} is being compared against again. It is a sign-in keyword, "
        "not a session label: the flow stamps nothing, so the token set carries "
        "the empty default and this branch is unreachable."
    )
    assert dead not in _produced(), (
        f"{dead!r} is now stamped on a token set. If that is deliberate, this "
        "test should be deleted and the recovery watchdog removed in 5.1.2 "
        "reconsidered — it was deleted because this label was never written."
    )


def test_the_removed_watchdog_has_no_callers_left() -> None:
    """The watchdog is gone; a dangling call would be an AttributeError at the
    top of every poll, and the loop's own guard would swallow it into a DEBUG
    line nobody reads."""
    for path in _SOURCES:
        src = path.read_text(encoding="utf-8")
        assert "_maybe_run_stale_watchdog" not in src, (
            f"{path.name} still references the removed watchdog"
        )
