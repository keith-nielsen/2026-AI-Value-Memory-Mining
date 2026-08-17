# SPDX-License-Identifier: Apache-2.0
"""Tests for the constitutional diff gate.

Ordered adversarially: the OVER-DENIAL cases come first, because a guard's
dangerous failure is refusing correct work. A suite that only proved the gate
catches a missing declaration would be the vacuous pass the Definition of Done
names -- it would pass against a gate that refuses everything.

The last test replays the last 25 merges of real history through the gate. That
is the only test here that exercises the geometry production actually presents;
the rest supply inputs a fixture chose.
"""
import importlib.util
import pathlib
import re
import subprocess

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
GATE = REPO / ".github" / "scripts" / "check-constitutional-impact.py"

_spec = importlib.util.spec_from_file_location("cimpact", GATE)
cimpact = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cimpact)

PROTECTED_SPECS = [
    "openspec/specs/access-control/spec.md",
    "openspec/specs/agent-integration/spec.md",
    "openspec/specs/maintenance/spec.md",
    "openspec/specs/naming-rules/spec.md",
    "openspec/specs/value-pipeline/spec.md",
    "openspec/specs/vault-structure/spec.md",
]

# Measured 2026-08-16 on main @ a9df354: files quoting `protects:` in PROSE only.
# A substring implementation refuses every one of them.
PROSE_ONLY = [
    "AGENTS.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    ".github/pull_request_template.md",
    ".github/workflows/ci.yml",
    "README.md",
    "openspec/constitution.md",
    "openspec/adr/0018-private-by-default-publish-guard.md",
    "openspec/adr/0024-bank-execute-pending-catalog.md",
    "openspec/adr/0025-permit-agent-claims-capture.md",
    "openspec/adr/0026-relocate-override-template-openspec-16.md",
    "openspec/adr/0027-release-object-per-tag-and-guard-conformance.md",
    "openspec/adr/0028-retire-effort-projections.md",
    "openspec/adr/0031-require-transcript-verification.md",
    "openspec/adr/0032-retire-daily-close-cycle.md",
    "openspec/adr/0033-open-logbook-write-scope.md",
    "openspec/adr/0034-branch-and-tag-rulesets.md",
]


def make_diff(*paths):
    return "".join(f"diff --git a/{p} b/{p}\n--- a/{p}\n+++ b/{p}\n@@ -1 +1 @@\n-x\n+y\n" for p in paths)


def run_gate(tmp_path, diff_text, root=REPO):
    d = tmp_path / "pr.diff"
    d.write_text(diff_text)
    return subprocess.run(
        ["python3", str(GATE), str(d), "--root", str(root)],
        capture_output=True, text=True,
    )


# --------------------------------------------------------------------------
# OVER-DENIAL: the cases where refusing would be the defect
# --------------------------------------------------------------------------

@pytest.mark.parametrize("path", PROSE_ONLY)
def test_prose_only_protects_mention_does_not_fire(tmp_path, path):
    """The 17 measured false positives a `grep protects:` gate would refuse.

    constitution.md is in this list deliberately: gating it would deadlock the
    document the gate exists to serve, and would have refused PR #85, which
    REMOVED six false enforcement claims.
    """
    r = run_gate(tmp_path, make_diff(path))
    assert r.returncode == 0, f"{path} wrongly treated as protected:\n{r.stdout}{r.stderr}"
    assert "not applicable" in r.stdout


def test_a_complete_constitution_override_is_never_refused_by_its_own_gate(tmp_path):
    """A guard that refuses the ceremony it demands discredits the protocol."""
    root = tmp_path / "repo"
    change = root / "openspec/changes/some-override"
    change.mkdir(parents=True)
    (root / "openspec/specs/maintenance").mkdir(parents=True)
    (root / "openspec/specs/maintenance/spec.md").write_text(
        "---\ncapability: maintenance\nprotects: [INV-2]\n---\nbody\n"
    )
    (change / "proposal.md").write_text(
        "**Change type:** `constitution-override`\n"
        "## Gate 1 — CHECK\nx\n## Gate 2 — PLAN\nx\n"
        "## Gate 3 — EXECUTE\nx\n## Gate 4 — RE-CHECK\nx\n"
    )
    r = run_gate(tmp_path, make_diff(
        "openspec/specs/maintenance/spec.md",
        "openspec/changes/some-override/proposal.md",
    ), root=root)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "ceremony present" in r.stdout


def test_the_real_template_is_recognised_as_a_ceremony():
    """Anchor the detector to the ACTUAL template, not to a fixture I wrote.

    The first draft of OVERRIDE_TYPE_RE matched a bare `Change type:
    constitution-override` and would have missed the real file, which wraps it as
    `**Change type:** \\`constitution-override\\``. A fixture agreeing with the
    regex proves only that one author wrote both.
    """
    text = (REPO / "openspec/templates/constitution-override/proposal.md").read_text()
    assert cimpact.OVERRIDE_TYPE_RE.search(text), "the real override template is not recognised"
    gates = {m.group("n") for m in cimpact.GATE_SECTION_RE.finditer(text)}
    assert gates >= {"1", "2", "3", "4"}, f"only found gates {sorted(gates)} in the real template"


def test_archive_sync_into_a_protected_spec_passes(tmp_path):
    """Archiving syncs deltas into protected specs BY CONSTRUCTION.

    Real shape from PR #64 (chore/archive-enforce-adr-reference-integrity), one of
    the 4 measured firing merges. A gate that refused this would refuse a routine
    ceremony step roughly every release cycle.
    """
    root = tmp_path / "repo"
    archived = root / "openspec/changes/archive/2026-08-11-enforce-adr-reference-integrity"
    archived.mkdir(parents=True)
    (root / "openspec/specs/maintenance").mkdir(parents=True)
    (root / "openspec/specs/maintenance/spec.md").write_text(
        "---\ncapability: maintenance\nprotects: [INV-2, INV-3, INV-6]\n---\nbody\n"
    )
    (archived / "proposal.md").write_text(
        "# Change\n\n```constitutional-impact\n"
        "touches: openspec/specs/maintenance/spec.md\n"
        "protects: [INV-2, INV-3, INV-6]\n"
        "overrides: none\n"
        "basis: ADD-only\n```\n"
    )
    r = run_gate(tmp_path, make_diff(
        "openspec/specs/maintenance/spec.md",
        "openspec/changes/archive/2026-08-11-enforce-adr-reference-integrity/proposal.md",
    ), root=root)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "overrides nothing" in r.stdout


def test_declaration_is_not_second_guessed(tmp_path):
    """`overrides: none` passes even where the diff is large.

    The gate must not develop an opinion about accuracy -- that is the human
    judgement Section 5 reserves.
    """
    root = tmp_path / "repo"
    change = root / "openspec/changes/ordinary-change"
    change.mkdir(parents=True)
    (root / "openspec/specs/value-pipeline").mkdir(parents=True)
    (root / "openspec/specs/value-pipeline/spec.md").write_text(
        "---\ncapability: value-pipeline\nprotects: [CONST-01, CONST-03]\n---\nbody\n"
    )
    (change / "proposal.md").write_text(
        "```constitutional-impact\noverrides: none\nbasis: whatever\n```\n"
    )
    r = run_gate(tmp_path, make_diff(
        "openspec/specs/value-pipeline/spec.md",
        "openspec/changes/ordinary-change/proposal.md",
    ), root=root)
    assert r.returncode == 0, r.stdout + r.stderr


def test_tier2_override_does_not_demand_a_ceremony(tmp_path):
    """constitution.md Section 2 puts INV-13 in Tier 2 -- ordinary change, no ceremony."""
    root = tmp_path / "repo"
    change = root / "openspec/changes/tier2-change"
    change.mkdir(parents=True)
    (root / "openspec/specs/maintenance").mkdir(parents=True)
    (root / "openspec/specs/maintenance/spec.md").write_text(
        "---\ncapability: maintenance\nprotects: [INV-2]\n---\nbody\n"
    )
    (change / "proposal.md").write_text(
        "```constitutional-impact\noverrides: [INV-13]\n```\n"
    )
    r = run_gate(tmp_path, make_diff(
        "openspec/specs/maintenance/spec.md",
        "openspec/changes/tier2-change/proposal.md",
    ), root=root)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Tier-2 only" in r.stdout


def test_tier2_exception_matches_the_constitution(tmp_path):
    """Drift detector for the ONE rule this gate encodes rather than imports.

    TIER_2_IDS is a fork of constitution.md Section 2's tier table. A fork with no
    merge is the class-9 defect, so this test fails the moment the constitution
    stops listing INV-13 as Tier 2.
    """
    text = (REPO / "openspec" / "constitution.md").read_text()
    tier2_row = [ln for ln in text.split("\n") if "Tier 2" in ln and "INV-13" in ln]
    assert tier2_row, "constitution.md Section 2 no longer lists INV-13 in Tier 2 -- TIER_2_IDS is stale"
    for other in cimpact.TIER_2_IDS:
        assert other in tier2_row[0], f"{other} is in TIER_2_IDS but not in the Tier-2 row"


# --------------------------------------------------------------------------
# The refusals the gate exists for
# --------------------------------------------------------------------------

@pytest.mark.parametrize("path", PROTECTED_SPECS)
def test_protected_spec_without_declaration_is_refused(tmp_path, path):
    r = run_gate(tmp_path, make_diff(path))
    assert r.returncode == 1, f"{path} should have been refused:\n{r.stdout}{r.stderr}"
    assert "REFUSED" in r.stderr


def test_refusal_names_file_tags_and_the_block_to_add(tmp_path):
    """A guard that reports only a verdict teaches its reader to route around it."""
    r = run_gate(tmp_path, make_diff("openspec/specs/maintenance/spec.md"))
    assert r.returncode == 1
    assert "openspec/specs/maintenance/spec.md" in r.stderr
    assert "INV-2" in r.stderr and "INV-3" in r.stderr and "INV-6" in r.stderr
    assert "```constitutional-impact" in r.stderr
    assert "pull-request body does not count" in r.stderr


def test_declaration_in_pr_body_only_is_refused(tmp_path):
    """The PR body is not a declaration channel: it can be edited after checks pass."""
    root = tmp_path / "repo"
    change = root / "openspec/changes/body-only"
    change.mkdir(parents=True)
    (root / "openspec/specs/maintenance").mkdir(parents=True)
    (root / "openspec/specs/maintenance/spec.md").write_text(
        "---\ncapability: maintenance\nprotects: [INV-2]\n---\nbody\n"
    )
    (change / "proposal.md").write_text("# Change\n\nNo declaration block here.\n")
    r = run_gate(tmp_path, make_diff(
        "openspec/specs/maintenance/spec.md",
        "openspec/changes/body-only/proposal.md",
    ), root=root)
    assert r.returncode == 1
    assert "in the tree" in r.stderr


def test_declared_override_without_ceremony_is_refused(tmp_path):
    root = tmp_path / "repo"
    change = root / "openspec/changes/sneaky"
    change.mkdir(parents=True)
    (root / "openspec/specs/vault-structure").mkdir(parents=True)
    (root / "openspec/specs/vault-structure/spec.md").write_text(
        "---\ncapability: vault-structure\nprotects: [CONST-05, INV-12]\n---\nbody\n"
    )
    (change / "proposal.md").write_text(
        "```constitutional-impact\noverrides: [CONST-05]\n```\n"
    )
    r = run_gate(tmp_path, make_diff(
        "openspec/specs/vault-structure/spec.md",
        "openspec/changes/sneaky/proposal.md",
    ), root=root)
    assert r.returncode == 1
    assert "CONST-05" in r.stderr
    assert "four gates" in r.stderr


def test_incomplete_ceremony_is_refused(tmp_path):
    """A constitution-override missing Gate 4 is not a ceremony."""
    root = tmp_path / "repo"
    change = root / "openspec/changes/half-ceremony"
    change.mkdir(parents=True)
    (root / "openspec/specs/maintenance").mkdir(parents=True)
    (root / "openspec/specs/maintenance/spec.md").write_text(
        "---\ncapability: maintenance\nprotects: [INV-2]\n---\nbody\n"
    )
    (change / "proposal.md").write_text(
        "**Change type:** `constitution-override`\n"
        "## Gate 1 — CHECK\nx\n## Gate 2 — PLAN\nx\n## Gate 3 — EXECUTE\nx\n"
        "```constitutional-impact\noverrides: [INV-2]\n```\n"
    )
    r = run_gate(tmp_path, make_diff(
        "openspec/specs/maintenance/spec.md",
        "openspec/changes/half-ceremony/proposal.md",
    ), root=root)
    assert r.returncode == 1


def test_malformed_input_fails_closed(tmp_path):
    r = subprocess.run(
        ["python3", str(GATE), str(tmp_path / "nope.diff")],
        capture_output=True, text=True,
    )
    assert r.returncode == 2


def test_frontmatter_must_open_the_file(tmp_path):
    """A `protects:` line below the opening fence is prose, not a tag."""
    p = tmp_path / "x.md"
    p.write_text("# Title\n\n---\nprotects: [INV-1]\n---\n")
    assert cimpact.frontmatter_protects(p) is None


# --------------------------------------------------------------------------
# Real geometry: replay actual history
# --------------------------------------------------------------------------

def _resolve_history_ref():
    """Return a ref with real merge history, or None under a shallow checkout.

    `actions/checkout@v7` defaults to depth 1 and a DETACHED head, so neither `main`
    nor `origin/main` exists on CI. The first version of this test shelled out to
    `main` with `check=True` and failed both fleet jobs on PR #89 -- a test that
    reproduced the author's geometry rather than the one production presents, which
    is the exact defect the suite above is written to avoid.
    """
    for ref in ("main", "origin/main"):
        r = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--verify", ref],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return ref
    return None


def test_replay_real_merges_agrees_with_the_protected_path_set():
    """Task 5.6 -- replay real merges and check the classifier against an INDEPENDENT
    computation of the same answer.

    Two defects this version exists to avoid, both shipped and both caught in
    production on 2026-08-16:

    1. **Ref existence is not history.** The first version required `main` to resolve.
       On a `pull_request` run it does not exist, so the test skipped -- correct by
       accident. On a `push` run `actions/checkout` CREATES the branch ref, so it
       resolved, and then `-25` returned 0 merges from a depth-1 clone. **That turned
       `main` red.** The precondition is sufficient HISTORY, not a resolvable name.

    2. **A snapshot is not an invariant.** It asserted `len(fired) == 4`, a measurement
       taken on one day against a window that slides with every merge. It was already
       one merge away from wrong when written.

    So: skip when history is absent, and assert a property that cannot rot -- the
    frontmatter classifier and the known protected-path set agree, over ~25 real diffs.
    A seventh protected spec, a dropped tag, or a broken parser all break the agreement;
    an ordinary merge does not.
    """
    ref = _resolve_history_ref()
    if ref is None:
        pytest.skip("shallow checkout: no main/origin/main to replay — this test is "
                    "meaningful only against a full clone (run it locally / in pre-flight)")
    merges = subprocess.run(
        ["git", "-C", str(REPO), "log", "--merges", "-25", "--format=%H", ref],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    if len(merges) < 25:
        pytest.skip(f"shallow clone: only {len(merges)} merge(s) reachable from {ref}, "
                    "need 25 — history is truncated, not missing")

    by_classifier, by_known_paths = set(), set()
    known = set(PROTECTED_SPECS)
    for sha in merges:
        diff = subprocess.run(
            ["git", "-C", str(REPO), "diff", "--no-renames", f"{sha}^1", sha],
            capture_output=True, text=True, check=True,
        ).stdout
        touched = cimpact.parse_diff_paths(diff)
        if any(cimpact.frontmatter_protects(REPO / p) is not None for p in touched):
            by_classifier.add(sha[:8])
        if touched & known:
            by_known_paths.add(sha[:8])

    assert by_classifier == by_known_paths, (
        "the frontmatter classifier and the known protected-path set disagree over real "
        f"history.\n  classifier-only: {sorted(by_classifier - by_known_paths)}\n"
        f"  paths-only:      {sorted(by_known_paths - by_classifier)}\n"
        "A spec gained or lost its protects: tag, or PROTECTED_SPECS is stale."
    )
    # Vacuity guard: agreement over an empty set proves nothing.
    assert by_classifier, ("no merge in the last 25 touched a protected spec — this replay "
                           "proved nothing; widen the window or check the subject set")
