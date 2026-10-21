# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""A release body that was 44 681 characters long.

Measured, not estimated: v5.1.0's published release body is **44 681
characters over 654 lines**, because ``release.yml`` pasted the version's whole
``CHANGELOG.md`` section into it verbatim. That body is what Home Assistant
shows in its update dialog and what HACS shows in the store listing, so on a
phone the part a reader needs first — what changed, and does it affect me —
sat under paragraphs of measurement and reasoning.

The reasoning is the point of the changelog and none of it is removed. It just
does not belong in a notification. So there are two documents for two
audiences:

* **the release body** — one line per change, each with its issue number and
  the people who reported or fixed it;
* **CHANGELOG.md** — unchanged, still the long form, linked from the body at
  the version's own tag so a reader (or a model summarising the release) is one
  click from the full account rather than from a shortened truth.

Nothing is maintained twice. Every entry already opens with a bold title, and
that title *is* the short form — these tests pin that the short body is derived
from it rather than written alongside it, because a second hand-kept list would
drift and no test would notice.
"""
from __future__ import annotations

import pathlib
import re
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_release_notes as brn  # noqa: E402


# ── fixtures ───────────────────────────────────────────────────────────────


def _changelog() -> str:
    return (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")


def _workflow() -> str:
    return (REPO_ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")


_HEADINGS = re.compile(r"^## \[([^\]]+)\]", re.MULTILINE)


def _newest_section_with_entries() -> tuple[str, str]:
    """``(heading, section_text)`` for the newest section that has entries.

    Deliberately not hardcoded to ``[Unreleased]``. Right after a release that
    section is empty, and every assertion below that iterates over its entries
    would then pass by iterating over nothing — the vacuous-pass shape this
    file exists to prevent elsewhere. Walking to the newest non-empty section
    means these tests keep testing something on every day of the cycle.
    """
    changelog = _changelog()
    for heading in _HEADINGS.findall(changelog):
        section = brn.section_for(changelog, heading)
        if brn.split_entries(section):
            return heading, section
    pytest.fail("no CHANGELOG section has any '- **…**' entries")


#: An entry opener, counted straight out of the source for comparison against
#: the generated body. Counted independently of split_entries on purpose: if
#: the splitter silently dropped entries, a count taken from the splitter
#: itself would agree with it and prove nothing.
_ENTRY_OPENER = re.compile(r"^- \*\*", re.MULTILINE)


# ── the shape the user reads ────────────────────────────────────────────────


def test_every_entry_becomes_exactly_one_line() -> None:
    """No change is dropped, and none is split in two.

    This is the assertion that makes "shorter" safe. A body that is short
    because it lost half the entries would satisfy every size bound here.
    """
    heading, section = _newest_section_with_entries()
    expected = len(_ENTRY_OPENER.findall(section))
    assert expected >= 1

    body = brn.build(_changelog(), "9.9.9", heading)
    produced = [ln for ln in body.splitlines() if ln.startswith("- ")]
    assert len(produced) == expected, (
        f"{expected} entries in [{heading}] produced {len(produced)} lines"
    )


def test_no_line_is_empty() -> None:
    """The first version emitted a bare ``- `` per group.

    The prose that sits between a group heading and its first bullet was being
    buffered as an entry, so each group opened with an empty bullet and the
    change count was inflated — 17 reported for 15 real changes.
    """
    heading, _ = _newest_section_with_entries()
    body = brn.build(_changelog(), "9.9.9", heading)
    for line in body.splitlines():
        if line.startswith("- "):
            assert line.strip() not in ("-", "- "), "an empty bullet is back"
            assert len(line) > 12, f"suspiciously short line: {line!r}"


def test_each_line_names_its_issue() -> None:
    """What was asked for: the ticket number, on the line.

    Enforced against the real changelog rather than a fixture, so an entry
    written without a reference fails here instead of reaching a release body
    where a reader cannot look the change up.
    """
    heading, _ = _newest_section_with_entries()
    body = brn.build(_changelog(), "9.9.9", heading)
    unnumbered = [
        ln for ln in body.splitlines()
        if ln.startswith("- ") and not re.search(r"#\d{2,6}", ln)
    ]
    assert not unnumbered, (
        "these changes carry no issue or PR number, so a reader cannot look "
        f"them up: {unnumbered}"
    )


def test_a_number_in_the_title_moves_out_of_it() -> None:
    """Some entries write their own number into the bold title.

    This was first fixed the other way round — the title kept ``(#1902)`` and
    the duplicate was stripped from the reference list — and that was wrong in
    a way only a line-by-line audit of the real output caught: the entry also
    cites ``#1661`` as precedent, so suppressing its own number left
    ``… battery again (#1902) — #1661``, whose only trailing number belongs to
    a different change. The number is moved out of the title instead, so the
    references list is complete and starts with the right one.
    """
    entry = (
        "- **Something is fixed again (#1902).** The body cites #1661 as the "
        "precedent it follows."
    )
    line = brn.short_line(entry)
    assert line.count("#1902") == 1, f"the number is duplicated: {line}"
    assert "again (#1902)" not in line, "the number is still inside the title"
    assert "#1902 #1661" in line, (
        f"the entry's own number must come first, not the precedent: {line}"
    )


def test_the_subject_reference_comes_first() -> None:
    """Source order puts a cited precedent in front of the actual subject.

    The real case: ``The e-mail code step no longer tells you your password is
    wrong`` cites two older hardenings before closing with its own issue, so
    the line read ``#1313 #1679 #1843`` — the number a reader reads first was
    a different, closed change from months earlier.
    """
    entry = (
        "- **The e-mail code step no longer tells you your password is "
        "wrong.** It was hardened for exactly this in "
        "[#1313](https://github.com/x/y/issues/1313) and "
        "[#1679](https://github.com/x/y/issues/1679). "
        "([#1843](https://github.com/x/y/issues/1843))"
    )
    line = brn.short_line(entry)
    assert "#1843 #1313 #1679" in line, line


def test_source_order_is_kept_when_the_entry_gives_no_signal() -> None:
    """The limit of the rule above, and why it is safe.

    Only 3 of 16 entries in this release close with a parenthetical, so the
    trailing form is a habit and not a convention. Entries with neither signal
    already list their subject first — the Scout entry below is about all
    three of its issues — so nothing is reordered for them. Reordering on a
    guess would misfire on the majority.
    """
    entry = (
        "- **An unmappable field stops asking three different people.** It "
        "raised the repair on Volkswagen ([#1831](https://github.com/x/y/issues/1831)), "
        "on an ID.7 ([#1838](https://github.com/x/y/issues/1838)) and on a "
        "Tavascan ([#1861](https://github.com/x/y/issues/1861))."
    )
    assert brn.subject_ref(entry) is None, "an entry with no signal claimed one"
    assert "#1831 #1838 #1861" in brn.short_line(entry)


def test_a_discussion_is_linked_not_hash_numbered() -> None:
    """A bare ``#1415`` would send the reader to the wrong object.

    GitHub numbers Discussions separately from issues and pull requests, so
    ``#1415`` in a release body autolinks to *issue* 1415 — which exists, and
    is somebody else's. The one line in this release whose subject is a
    discussion pointed at an unrelated issue, which is a wrong destination
    rather than an untidy one.
    """
    entry = (
        "- **The Vehicle Status sensor was blank.** @someone reported it on a "
        "Tavascan ([discussion #1415](https://github.com/x/y/discussions/1415)), "
        "and #923 already guaranteed the opposite."
    )
    line = brn.short_line(entry)
    assert "[discussion #1415](https://github.com/x/y/discussions/1415)" in line, line
    assert " #1415" not in line.replace("[discussion #1415]", ""), (
        f"the discussion is still emitted as a bare issue reference: {line}"
    )
    assert "#923" in line, "the ordinary issue reference was lost"


def test_every_discussion_reference_in_the_real_section_is_linked() -> None:
    """Pinned against the shipping changelog, not only a fixture: an entry
    added later with a discussion link must not regress to a bare number."""
    heading, section = _newest_section_with_entries()
    body = brn.build(_changelog(), "9.9.9", heading)
    for num in re.findall(r"/discussions/(\d+)", section):
        assert f"discussion #{num}" in body or f"#{num}" not in body, (
            f"discussion {num} appears as a bare #{num}, which links to issue "
            f"{num} instead"
        )


def test_a_wrapped_title_is_read_whole() -> None:
    """Titles wrap across source lines. Reading only the first line would
    truncate most of them mid-sentence, which is how this was first written."""
    entry = (
        "- **The charge-timer sensors and the charging calendar are no\n"
        "  longer off by your UTC offset.** @someone measured it.\n"
    )
    title = brn.title_of(entry)
    assert title.endswith("off by your UTC offset"), title
    assert "\n" not in title


def test_contributors_are_credited_and_the_maintainer_is_not() -> None:
    """Also what was asked for. The maintainer's own handle is excluded —
    thanking yourself in your own release notes reads badly and it is on every
    entry, so it would crowd out the people who actually reported things."""
    entry = (
        "- **A thing.** @somebody reported it, @another confirmed it, and "
        "@its-me-prash fixed it. @somebody also sent diagnostics."
    )
    line = brn.short_line(entry)
    assert "thanks @somebody, @another" in line, line
    assert "its-me-prash" not in line
    assert line.count("@somebody") == 1, "a handle is credited twice"


def test_many_references_are_capped_not_dropped_silently() -> None:
    """A line with eight numbers on it is not scannable, which is the whole
    point of the short form. The overflow is counted rather than discarded, so
    the line never claims to list them all."""
    entry = "- **A thing.** See #11, #22, #33, #44, #55, #66."
    line = brn.short_line(entry)
    shown = re.findall(r"#\d+", line)
    assert len(shown) == brn._MAX_REFS, line
    assert "+2" in line, f"two references vanished without a trace: {line}"


# ── the long form stays reachable ──────────────────────────────────────────


def test_the_long_form_is_linked_at_the_version_tag() -> None:
    """``main`` would drift: a reader opening v5.2.0's notes in six months must
    land on what v5.2.0 actually said, not on the current file."""
    heading, _ = _newest_section_with_entries()
    body = brn.build(_changelog(), "5.2.0", heading)
    assert "/blob/v5.2.0/CHANGELOG.md" in body, (
        "the changelog link is missing or not pinned to the version's tag"
    )
    assert "CHANGELOG.md" in body


def test_the_body_says_how_many_changes_the_long_form_covers() -> None:
    """So a reader can tell the short body is a summary of a known quantity
    rather than a selection someone made."""
    heading, section = _newest_section_with_entries()
    expected = len(_ENTRY_OPENER.findall(section))
    body = brn.build(_changelog(), "9.9.9", heading)
    assert f"all {expected} change" in body, (
        f"the body does not state the real change count ({expected})"
    )


def test_the_short_body_is_actually_short() -> None:
    """A ratio rather than a character bound, so it scales with the release
    instead of needing a new magic number every cycle.

    v5.1.0's verbatim body was 44 681 characters; the same content through this
    builder is a few thousand. Anything above a quarter of the section length
    means the short form has started growing back into the long one.
    """
    heading, section = _newest_section_with_entries()
    body = brn.build(_changelog(), "9.9.9", heading)
    assert len(body) < len(section) / 4, (
        f"short body is {len(body)} chars against a {len(section)}-char "
        "section — it is no longer a summary"
    )


def test_an_empty_or_missing_section_refuses_rather_than_guessing() -> None:
    """The workflow catches this and falls back to the link. What must not
    happen is a release published with a confidently empty change list."""
    with pytest.raises(SystemExit):
        brn.build("## [1.0.0]\n\nnothing here\n", "9.9.9")
    with pytest.raises(SystemExit):
        brn.build("## [1.0.0]\n\n### Fixed\n\nprose, no entries\n", "1.0.0")


# ── the workflow actually uses it ──────────────────────────────────────────


def _workflow_code() -> str:
    """The workflow's python with comment lines removed.

    Comments are stripped before any of the assertions below look at this,
    because three times in this batch a text gate was satisfied by the very
    comment explaining the fix. The prose below mentions "the entire CHANGELOG
    section verbatim"; that must not be able to pass for the code doing it.
    """
    return "\n".join(
        ln for ln in _workflow().splitlines() if not ln.strip().startswith("#")
    )


def test_the_workflow_builds_the_short_body() -> None:
    code = _workflow_code()
    assert "from build_release_notes import build" in code, (
        "release.yml no longer calls the short-notes builder"
    )
    assert "build_short_notes(changelog, version)" in code


def test_the_workflow_no_longer_pastes_the_section_verbatim() -> None:
    """The actual regression guard. Everything else here could pass while the
    workflow quietly went back to appending the whole section."""
    code = _workflow_code()
    assert "changelog_section" not in code, (
        "the verbatim CHANGELOG section is being assembled again; that is "
        "what produced the 44 681-character body"
    )


def test_the_workflow_survives_a_version_with_no_section() -> None:
    """A tag whose changelog section is missing must still publish a release,
    with the link in place of the list. Failing the tag at that point would
    leave a tag with no release and no vag_connect.zip."""
    code = _workflow_code()
    assert "except SystemExit" in code, (
        "the builder's refusal is no longer caught; a missing section would "
        "now fail the release job after the tag already exists"
    )
    assert "for details._" in code, "the fallback link is gone"


def test_the_builder_ships_with_the_repository() -> None:
    """The workflow imports it by path from the checkout, so it has to be a
    tracked file rather than something that exists only on one machine."""
    assert (REPO_ROOT / "scripts/build_release_notes.py").is_file()
    code = _workflow_code()
    assert 'sys.path.insert(0, "scripts")' in code
