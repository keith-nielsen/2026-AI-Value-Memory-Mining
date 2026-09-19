# SPDX-License-Identifier: Apache-2.0
"""The sanctioned write-endpoint set has ONE source of truth, and the guards import it.

WHY THIS EXISTS. `docs/version-control-legal-moves.md` §2b enumerates every REST write this estate
sanctions. Both guards need that set at runtime, and neither may read the doc: they are stdlib-only,
deterministic, and render into roots that have no `docs/` directory (INV-6). So each carries a copy —
and a copy with no equality test is the estate's class-9 defect, a rule restated instead of imported.
This module is the equality.

WHAT MAKES IT AN IMPORT RATHER THAN A RESTATEMENT. No endpoint list is authored here. The doc is
parsed, each guard's constant is read out of its literate note, and the three are compared. Adding a
row to any one copy fails until the others agree, which is the only structure that keeps a
"single source of truth" true after the commit that declared it.

THE NOTES ARE THE SOURCE, NOT THE HOOKS. `vault-template/99-Operations/scripts/*.md` is what `render`
deploys (INV-3); `.claude/hooks/*.py` is its output. Reading the hook would test the deployed copy
and pass while the note — the thing a change actually edits — had drifted.

SCOPE. Set equality only: the same methods against the same endpoint templates, and the same
outbound marking. Whether a guard then ENFORCES its set is §3's business and has its own tests.
"""
import ast
import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
DOC = REPO / "docs/version-control-legal-moves.md"
NOTES = REPO / "vault-template/99-Operations/scripts"
INVOCATION_NOTE = NOTES / "gh-invocation-guard-script.md"
OUTBOUND_NOTE = NOTES / "outbound-publish-guard-script.md"

FIELDS = ("method", "endpoint", "runs", "authority", "precondition", "outbound")
EXCLUDED_FIELDS = ("method", "endpoint", "reason")
WRITE_METHODS = {"POST", "PATCH", "PUT", "DELETE"}


def parse_doc_block(text):
    """-> list of row dicts from the ```gh-write-endpoints fence. Raises if the fence is absent.

    A missing fence is a failure, never an empty set: 'no rows' and 'no block' must not look alike,
    or deleting the block would read as 'nothing is sanctioned' and pass every comparison below.
    """
    m = re.search(r"^```gh-write-endpoints[ \t]*\r?\n(.*?)^```", text, re.S | re.M)
    if not m:
        raise AssertionError("docs/version-control-legal-moves.md carries no "
                             "```gh-write-endpoints block — the set has no source of truth")
    rows = []
    for lineno, line in enumerate(m.group(1).splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        assert len(parts) == len(FIELDS), (
            f"row {lineno} has {len(parts)} fields, expected {len(FIELDS)} {FIELDS}: {line!r}")
        row = dict(zip(FIELDS, parts))
        assert row["method"] in WRITE_METHODS, (
            f"row {lineno}: {row['method']!r} is not a write method — GET is unconstrained and does "
            f"not belong in the sanctioned-write set")
        assert row["endpoint"].startswith("/"), f"row {lineno}: endpoint must be rooted: {row!r}"
        assert row["outbound"] in {"yes", "no"}, (
            f"row {lineno}: outbound must be yes or no, got {row['outbound']!r}")
        rows.append(row)
    assert rows, "the ```gh-write-endpoints block is empty"
    return rows


def parse_excluded_block(text):
    """-> list of row dicts from the ```gh-write-endpoints-excluded fence.

    Absence from the sanctioned set is ALREADY a refusal — this block exists so that an endpoint
    left out by decision is distinguishable from one left out by oversight. Parsed, not merely
    written, so the two sets can be held disjoint mechanically.
    """
    m = re.search(r"^```gh-write-endpoints-excluded[ \t]*\r?\n(.*?)^```", text, re.S | re.M)
    if not m:
        raise AssertionError("docs/version-control-legal-moves.md carries no "
                             "```gh-write-endpoints-excluded block — a deliberate exclusion and an "
                             "oversight are then indistinguishable")
    rows = []
    for lineno, line in enumerate(m.group(1).splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        assert len(parts) == len(EXCLUDED_FIELDS), (
            f"excluded row {lineno} has {len(parts)} fields, expected {EXCLUDED_FIELDS}: {line!r}")
        row = dict(zip(EXCLUDED_FIELDS, parts))
        assert row["reason"], f"excluded row {lineno} carries no reason — then it is an oversight"
        rows.append(row)
    assert rows, "the ```gh-write-endpoints-excluded block is empty"
    return rows


def note_constant(note_path, name):
    """Read one module-level constant out of a literate note's python fence.

    Evaluated with `ast.literal_eval`, not `exec`: the value must be a literal, so a test cannot be
    made to pass by a guard computing its set at import time.
    """
    assert note_path.exists(), f"{note_path.relative_to(REPO)} is missing"
    m = re.search(r"^## Implementation\s*\n```python\n(.*?)^```",
                  note_path.read_text(encoding="utf-8"), re.S | re.M)
    assert m, f"no python implementation block in {note_path.name}"
    tree = ast.parse(m.group(1))
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else []
        for t in targets:
            if getattr(t, "id", None) == name:
                try:
                    return {tuple(v) for v in ast.literal_eval(node.value)}
                except ValueError as exc:  # pragma: no cover - reported, never swallowed
                    raise AssertionError(
                        f"{name} in {note_path.name} is not a literal: {exc}") from exc
    raise AssertionError(
        f"{note_path.relative_to(REPO)} carries no `{name}` constant — the guard cannot hold the "
        f"sanctioned set it is supposed to import")


@pytest.fixture(scope="module")
def doc_rows():
    return parse_doc_block(DOC.read_text(encoding="utf-8"))


def test_the_block_parses_and_has_a_denominator(doc_rows):
    """A comparison against an unstated number of rows hides a silent deletion."""
    assert len(doc_rows) >= 5, f"only {len(doc_rows)} sanctioned writes parsed — the block is thin"
    endpoints = [(r["method"], r["endpoint"]) for r in doc_rows]
    assert len(endpoints) == len(set(endpoints)), f"duplicate rows in the block: {endpoints}"


def test_invocation_guard_carries_the_whole_set(doc_rows):
    """THE EQUALITY. The guard's list and the doc's block are the same set, both directions."""
    documented = {(r["method"], r["endpoint"]) for r in doc_rows}
    carried = note_constant(INVOCATION_NOTE, "SANCTIONED_WRITES")
    assert carried == documented, (
        "the invocation guard and the doc disagree about the sanctioned write set.\n"
        f"  in the doc, not the guard: {sorted(documented - carried)}\n"
        f"  in the guard, not the doc: {sorted(carried - documented)}")


def test_outbound_guard_carries_the_outbound_subset(doc_rows):
    """The outbound rail's copy is the `outbound: yes` rows — no more, and no fewer.

    Fewer, and a publishing write escapes the INV-14 ask: measured 2026-09-19, the REST release
    form passed the guard in silence while its subcommand spelling raised the full banner.
    More, and the banner fires on writes that publish nothing, which teaches the operator to
    approve it without reading — the failure mode a guard cannot recover from.
    """
    documented = {(r["method"], r["endpoint"]) for r in doc_rows if r["outbound"] == "yes"}
    carried = note_constant(OUTBOUND_NOTE, "OUTBOUND_ENDPOINTS")
    assert carried == documented, (
        "the outbound guard and the doc disagree about which endpoints publish.\n"
        f"  publishes per the doc, missing from the guard: {sorted(documented - carried)}\n"
        f"  in the guard, not marked outbound in the doc: {sorted(carried - documented)}")


def test_invocation_guard_carries_the_excluded_set_verbatim():
    """The guard names the exclusions so its refusal can teach — and that copy is held equal too.

    The guard needs this set only for its MESSAGE: absence from SANCTIONED_WRITES already refuses.
    But a message that names a decision is itself a claim about the record, and a claim that drifts
    from the record is worse than a bare refusal.
    """
    documented = {(r["method"], r["endpoint"])
                  for r in parse_excluded_block(DOC.read_text(encoding="utf-8"))}
    carried = note_constant(INVOCATION_NOTE, "EXCLUDED_WRITES")
    assert carried == documented, (
        "the invocation guard and the doc disagree about what is excluded by decision.\n"
        f"  excluded in the doc, not the guard: {sorted(documented - carried)}\n"
        f"  excluded in the guard, not the doc: {sorted(carried - documented)}")


def test_every_outbound_row_is_also_in_the_full_set(doc_rows):
    """The subset relation itself, stated so a future edit cannot quietly break it."""
    full = {(r["method"], r["endpoint"]) for r in doc_rows}
    outbound = {(r["method"], r["endpoint"]) for r in doc_rows if r["outbound"] == "yes"}
    assert outbound <= full


def test_excluded_endpoints_are_not_in_the_sanctioned_set(doc_rows):
    """The two blocks are disjoint, and the guards hold neither excluded row.

    This is the assertion that makes the exclusion a control rather than a paragraph: admitting a
    ruleset write later fails here until its row is removed from the excluded block, which is where
    the reasoning for keeping it out is written down. The decision cannot be reversed by accident.
    """
    sanctioned = {(r["method"], r["endpoint"]) for r in doc_rows}
    excluded = {(r["method"], r["endpoint"])
                for r in parse_excluded_block(DOC.read_text(encoding="utf-8"))}

    overlap = sanctioned & excluded
    assert not overlap, (
        f"these endpoints are both sanctioned and excluded: {sorted(overlap)}. "
        f"One of the two blocks is wrong, and the guards will follow the sanctioned one.")

    for note, const in ((INVOCATION_NOTE, "SANCTIONED_WRITES"),
                        (OUTBOUND_NOTE, "OUTBOUND_ENDPOINTS")):
        leaked = note_constant(note, const) & excluded
        assert not leaked, (
            f"{note.name} carries {sorted(leaked)}, which the doc excludes by decision — "
            f"a guard must never be wider than the set it imports")


def test_the_ruleset_control_plane_is_excluded(doc_rows):
    """Named specifically, because this one is the reason the excluded block exists.

    GitHub rulesets are the only server-side control in the stack (ADR-0034) and a ruleset PUT
    replaces the entire rules array (ADR-0038). A test that only checked 'the blocks are disjoint'
    would still pass if someone deleted the ruleset rows from BOTH blocks and added them to the
    sanctioned set in one edit; this one names what must stay out.
    """
    excluded = {(r["method"], r["endpoint"])
                for r in parse_excluded_block(DOC.read_text(encoding="utf-8"))}
    for method in ("PUT", "PATCH", "DELETE"):
        assert (method, "/repos/{slug}/rulesets/{id}") in excluded, (
            f"{method} on a ruleset is no longer listed as excluded. If that is deliberate it is a "
            f"Tier-0 widening: the agent channel would be able to rewrite the control that binds "
            f"the operator and the admin. It belongs in a change with its own Gate 4, never here.")
    sanctioned = {r["endpoint"] for r in doc_rows}
    assert "/repos/{slug}/rulesets/{id}" not in sanctioned


def test_a_divergent_copy_is_detected(tmp_path):
    """The instrument is shown to FAIL, on a fixture, rather than asserted to work.

    An equality test that has only ever been observed green is not evidence that it would catch
    the drift it exists for — the premise of this whole change.
    """
    doc = tmp_path / "doc.md"
    doc.write_text(
        "```gh-write-endpoints\n"
        "POST   | /repos/{slug}/pulls    | operator | operator | none | no\n"
        "POST   | /repos/{slug}/releases | operator | operator | none | yes\n"
        "```\n", encoding="utf-8")
    rows = parse_doc_block(doc.read_text(encoding="utf-8"))
    documented = {(r["method"], r["endpoint"]) for r in rows}
    drifted = {("POST", "/repos/{slug}/pulls")}  # a guard that lost the releases row
    assert drifted != documented, "the comparison cannot see a dropped row"
    assert documented - drifted == {("POST", "/repos/{slug}/releases")}

    missing = tmp_path / "empty.md"
    missing.write_text("no fence here\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="no.*gh-write-endpoints block"):
        parse_doc_block(missing.read_text(encoding="utf-8"))
