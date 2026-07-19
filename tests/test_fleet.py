"""Behaviour tests for the Layer-0 script fleet.

These formalise the batteries proven by hand during the vault_lib remediation (ADR-0023)
and by `.github/scripts/validate-scripts.sh`: the close-day lifecycle and its gates, the
refine executor's whole-proposal pre-flight and batch isolation, scoped commit ownership,
the render fence lint, env-free root resolution, and the shell-pair move gates. Every case
drives the deployed script as a subprocess — the runtime the fleet ships in.
"""

import json
import subprocess
import sys
import textwrap

import pytest

# Fleet exit-code contract (vault_lib): 0 ok/no-op · 1 violation · 2 needs-input · 3 gate-blocked.
EXIT_OK, EXIT_VIOLATION, EXIT_NEEDS_INPUT, EXIT_BLOCKED = 0, 1, 2, 3

def make_proposal(fleet, name, **fields):
    fleet.write(f"20-Claims/_refine-approved/{name}.json", json.dumps(fields, indent=2))


def good_create(target="40-Treasury/good-durable-insight.md", **over):
    p = {
        "target_note": target,
        "mode": "create",
        "insight_md": "Durable value.",
        "provenance_md": "Tried X, kept Y.",
        "index_links": ["40-Treasury/Catalog/technology-domain-index.md"],
        "frontmatter": {"pillars": ["technology"], "grade": "gold", "crucible": False},
    }
    p.update(over)
    return p


# --------------------------------------------------------------------------------------
# baseline: the fixture renders a fleet that reconciles with zero drift
# --------------------------------------------------------------------------------------

def test_fixture_renders_zero_drift(fleet):
    r = fleet.run("vault-render.py", "reconcile")
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert "DRIFT" not in r.stdout
    assert "VIOLATION" not in r.stdout


# --------------------------------------------------------------------------------------
# refine executor: whole-proposal pre-flight, no partial writes, batch isolation
# --------------------------------------------------------------------------------------

def test_bank_applies_conforming_proposal_atomically(fleet):
    make_proposal(fleet, "a-good", **good_create())
    fleet.setup_commit("queue proposal")
    r = fleet.run("vault-refine-execute.py")
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert fleet.exists("40-Treasury/good-durable-insight.md")
    note = fleet.read("40-Treasury/good-durable-insight.md")
    assert "grade: gold" in note
    assert fleet.head_message() == "bank: good-durable-insight"
    # one atomic commit: the note, its Catalog index, and the consumed proposal (a deletion)
    files = set(fleet.head_files())
    assert "40-Treasury/good-durable-insight.md" in files
    assert "40-Treasury/Catalog/technology-domain-index.md" in files
    assert "20-Claims/_refine-approved/a-good.json" in files
    assert not fleet.exists("20-Claims/_refine-approved/a-good.json")


def test_bank_rejects_malformed_json_without_write(fleet):
    fleet.write("20-Claims/_refine-approved/broken.json", "{ this is not json")
    fleet.setup_commit("queue broken proposal")
    r = fleet.run("vault-refine-execute.py")
    assert r.returncode == EXIT_VIOLATION
    assert "REJECT" in r.stdout and "invalid JSON" in r.stdout


def test_bank_rejects_inv9_overwrite(fleet):
    fleet.write("40-Treasury/existing-durable-note.md", "PRECIOUS existing content\n")
    make_proposal(fleet, "collide", **good_create(target="40-Treasury/existing-durable-note.md"))
    fleet.setup_commit("existing + colliding proposal")
    r = fleet.run("vault-refine-execute.py")
    assert r.returncode == EXIT_VIOLATION
    assert "INV-9" in r.stdout
    # the existing note is untouched — no partial write clobbered it
    assert fleet.read("40-Treasury/existing-durable-note.md") == "PRECIOUS existing content\n"


def test_bank_rejects_missing_index_link_before_writing(fleet):
    make_proposal(fleet, "dangling", **good_create(
        index_links=["40-Treasury/Catalog/does-not-exist-index.md"]))
    fleet.setup_commit("proposal with dangling link")
    r = fleet.run("vault-refine-execute.py")
    assert r.returncode == EXIT_VIOLATION
    assert "index link target missing" in r.stdout
    # pre-flight rejects the whole proposal — the note is never written
    assert not fleet.exists("40-Treasury/good-durable-insight.md")


def test_bank_rejects_path_traversal(fleet):
    make_proposal(fleet, "escape", **good_create(target="40-Treasury/../../escaped.md"))
    fleet.setup_commit("traversal proposal")
    r = fleet.run("vault-refine-execute.py")
    assert r.returncode == EXIT_VIOLATION
    assert "escapes 40-Treasury" in r.stdout
    assert not (fleet.vault.parent / "escaped.md").exists()


def test_bank_defaults_empty_index_links_to_pending_catalog(fleet):
    # INV-12 reachability: an explicit empty index_links is defaulted to the holding index
    # (which the template ships), not rejected and not left an orphan.
    fleet.write("40-Treasury/Catalog/pending-catalog-index.md",
                "---\ntype: index\npillar: pending\n---\n# Pending-catalog index\n\n## Awaiting catalog\n")
    make_proposal(fleet, "uncataloged", **good_create(index_links=[]))
    fleet.setup_commit("queue proposal with empty index_links")
    r = fleet.run("vault-refine-execute.py")
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert fleet.exists("40-Treasury/good-durable-insight.md")
    # linked into the holding queue, not orphaned
    assert "[[good-durable-insight]]" in fleet.read("40-Treasury/Catalog/pending-catalog-index.md")
    # atomic bank: the holding index rode the commit and the proposal was consumed
    files = set(fleet.head_files())
    assert "40-Treasury/Catalog/pending-catalog-index.md" in files
    assert not fleet.exists("20-Claims/_refine-approved/uncataloged.json")


def test_bank_rejects_bad_vocabulary(fleet):
    make_proposal(fleet, "badgrade", **good_create(
        target="40-Treasury/bad-grade-note.md",
        frontmatter={"pillars": ["technology"], "grade": "platinum", "crucible": False}))
    fleet.setup_commit("bad-grade proposal")
    r = fleet.run("vault-refine-execute.py")
    assert r.returncode == EXIT_VIOLATION
    assert "grade must be one of" in r.stdout
    assert not fleet.exists("40-Treasury/bad-grade-note.md")


def test_bank_rejects_append_to_missing_target(fleet):
    make_proposal(fleet, "append-missing",
                  target_note="40-Treasury/no-such-note.md", mode="append",
                  insight_md="more", provenance_md="p", index_links=[])
    fleet.setup_commit("append-to-missing proposal")
    r = fleet.run("vault-refine-execute.py")
    assert r.returncode == EXIT_VIOLATION
    assert "append target missing" in r.stdout


def _bank_seed(fleet):
    """Bank the default create note (linked once into the technology index)."""
    make_proposal(fleet, "seed", **good_create())
    fleet.setup_commit("queue create")
    assert fleet.run("vault-refine-execute.py").returncode == EXIT_OK


def test_bank_append_does_not_duplicate_existing_catalog_link(fleet):
    _bank_seed(fleet)
    idx = "40-Treasury/Catalog/technology-domain-index.md"
    assert fleet.read(idx).count("[[good-durable-insight]]") == 1
    # append to the already-catalogued note, naming the index it is already in
    make_proposal(fleet, "errata", target_note="40-Treasury/good-durable-insight.md",
                  mode="append", insight_md="## Errata\nCorrection.",
                  provenance_md="appended later", index_links=[idx])
    fleet.setup_commit("queue append")
    r = fleet.run("vault-refine-execute.py")
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert "## Errata" in fleet.read("40-Treasury/good-durable-insight.md")  # content appended
    # idempotent: the catalog bullet appears exactly once, not twice
    assert fleet.read(idx).count("[[good-durable-insight]]") == 1


def test_bank_append_still_links_a_genuinely_new_index(fleet):
    _bank_seed(fleet)
    new_idx = "40-Treasury/Catalog/second-home-index.md"
    fleet.write(new_idx, "---\ntype: index\npillar: technology\n---\n# Second home\n")
    make_proposal(fleet, "cross", target_note="40-Treasury/good-durable-insight.md",
                  mode="append", insight_md="more", provenance_md="p", index_links=[new_idx])
    fleet.setup_commit("queue append to a new index")
    r = fleet.run("vault-refine-execute.py")
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    # idempotency does not block a fresh index — the note is linked into it
    assert "[[good-durable-insight]]" in fleet.read(new_idx)


def test_bank_batch_isolation_one_bad_one_good(fleet):
    make_proposal(fleet, "a-good", **good_create(target="40-Treasury/batch-good-note.md"))
    make_proposal(fleet, "b-bad", **good_create(
        target="40-Treasury/batch-bad-note.md",
        frontmatter={"pillars": ["technology"], "grade": "platinum", "crucible": False}))
    fleet.setup_commit("mixed batch")
    r = fleet.run("vault-refine-execute.py")
    assert r.returncode == EXIT_VIOLATION            # any reject → exit 1
    assert fleet.exists("40-Treasury/batch-good-note.md")   # good one still applied
    assert not fleet.exists("40-Treasury/batch-bad-note.md")
    assert "REJECT" in r.stdout and "b-bad.json" in r.stdout


# --------------------------------------------------------------------------------------
# vault_lib.commit_paths: no-op guard + unchanged pathspec produce no commit
# --------------------------------------------------------------------------------------

def test_commit_paths_noop_and_unchanged(fleet):
    code = textwrap.dedent(f"""
        import sys, pathlib
        sys.path.insert(0, {str(fleet.home / "bin")!r})
        from vault_lib import commit_paths, find_vault_root
        vault = find_vault_root()
        commit_paths(vault, [], "empty pathspec must not commit")
        idx = vault / "40-Treasury" / "Catalog" / "technology-domain-index.md"
        commit_paths(vault, [idx], "already committed + unmodified must not commit")
    """)
    before = fleet.commit_count()
    r = subprocess.run([sys.executable, "-c", code], cwd=str(fleet.vault),
                       env=fleet.env(), capture_output=True, text=True)
    assert r.returncode == EXIT_OK, r.stderr
    assert fleet.commit_count() == before          # neither call produced a commit


# --------------------------------------------------------------------------------------
# render fence lint: a note with ≠1 code fence is a VIOLATION (nothing rendered for it)
# --------------------------------------------------------------------------------------

def test_render_fence_lint_flags_double_fence(fleet):
    note = "99-Operations/scripts/ore-detect-script.md"
    fleet.write(note, fleet.read(note) + "\n```python\nprint('stowaway second fence')\n```\n")
    r = fleet.run("vault-render.py", "reconcile")
    assert r.returncode == EXIT_VIOLATION
    assert "VIOLATION" in r.stdout
    assert "ore-detect-script.md" in r.stdout


# --------------------------------------------------------------------------------------
# env-free root resolution (ADR-0023): cwd marker-walk vs. no-vault BLOCKED
# --------------------------------------------------------------------------------------

def test_bare_run_resolves_root_from_cwd(fleet):
    # no VAULT_ROOT in the environment — resolution must walk up from cwd to the marker
    r = fleet.run("vault-refine-detect.py", vault_root=False, cwd=fleet.vault)
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert "queued" in r.stdout


def test_bare_run_outside_any_vault_blocks(fleet):
    # cwd is the sandbox HOME (no 99-Operations marker at or above it) and no VAULT_ROOT
    r = fleet.run("vault-render.py", "reconcile", vault_root=False, cwd=fleet.home)
    assert r.returncode == EXIT_BLOCKED
    assert "BLOCKED" in (r.stdout + r.stderr)


# --------------------------------------------------------------------------------------
# shell-pair move gates (slag / dump): naming boundary, src/dest gates, scoped commit
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("script,dest,verb", [
    ("vault-slag.sh", "70-Tailings", "slag"),
    ("vault-dump.sh", "71-Spoil", "dump"),
])
def test_shell_pair_moves_effort_scoped(fleet, script, dest, verb):
    slug = "sample-effort-site"
    fleet.write(f"30-Sites/{slug}/sample-effort-site.md", "# effort\nwork\n")
    fleet.setup_commit("add site")
    # unrelated, uncommitted working-tree content that a scoped commit must NOT sweep
    # (re-exemplified here from the retired close-day case — ADR-0032)
    fleet.write("30-Sites/unrelated-dirty-note.md", "dirty working copy\n")
    r = fleet.run(script, slug)
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert not fleet.exists(f"30-Sites/{slug}")
    assert fleet.exists(f"{dest}/{slug}/sample-effort-site.md")
    assert fleet.head_message().startswith(f"{verb}:")
    # the commit carries only the moved effort — the unrelated file is not swept in
    assert all("unrelated-dirty-note" not in f for f in fleet.head_files()), fleet.head_files()
    porcelain = fleet.git("status", "--porcelain").stdout
    assert "30-Sites/unrelated-dirty-note.md" in porcelain


@pytest.mark.parametrize("script", ["vault-slag.sh", "vault-dump.sh"])
def test_shell_pair_blocks_missing_source(fleet, script):
    r = fleet.run(script, "no-such-effort-site")
    assert r.returncode == EXIT_BLOCKED
    assert "BLOCKED" in (r.stdout + r.stderr)


@pytest.mark.parametrize("script", ["vault-slag.sh", "vault-dump.sh"])
def test_shell_pair_rejects_unsafe_name(fleet, script):
    # a forbidden character trips the INV-11 name-safety gate (vault_naming.py --check)
    # before any source lookup — the move never starts
    r = fleet.run(script, "bad:slug")
    assert r.returncode == EXIT_VIOLATION


# --------------------------------------------------------------------------------------
# vocabulary integrity: PILLARS tokens are kebab slugs (ADR-0029)
# --------------------------------------------------------------------------------------

KNOWLEDGE_TMPL = """---
type: knowledge
title: {title}
pillars: [{pillar}]
grade: gold
stage: refined
crucible: false
created: 2026-07-17
updated: 2026-07-17
---
# {title}

Durable value.
"""


def pin_pillars(fleet, value):
    """Pin PILLARS in the sandbox's private config.env.

    vault_lib._CONFIGS reads ("config.defaults.env", "config.env") in order, later wins —
    so this overrides the framework default the way a real adopter would, by editing their
    private config rather than the public tracked one.
    """
    cfg = fleet.vault / "99-Operations" / "config.env"
    cfg.write_text(cfg.read_text() + f'\nexport PILLARS="{value}"\n')


def test_lint_accepts_default_pillar_vocabulary(fleet):
    # the shipped example default: six single-word tokens, all valid kebab slugs
    r = fleet.run("vault-lint.py")
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert "LINT PILLARS" not in r.stdout


@pytest.mark.parametrize("token,why", [
    ("Mental_Health", "uppercase + underscore"),
    ("CON", "reserved device name"),
    ("-lead", "leading hyphen"),
])
def test_lint_rejects_malformed_pillar_token(fleet, token, why):
    pin_pillars(fleet, f"{token} financial social technology calling")
    r = fleet.run("vault-lint.py")
    assert r.returncode == EXIT_VIOLATION, f"{why}: {r.stdout + r.stderr}"
    assert "LINT PILLARS" in r.stdout, r.stdout
    assert token in r.stdout, r.stdout


def test_lint_reports_bad_vocabulary_without_cascading(fleet):
    # a malformed vocabulary must surface as ONE vocabulary violation, not as a per-note
    # frontmatter pile-up: every note's `pillars` would fail the subset check against it.
    pin_pillars(fleet, "Mental_Health financial social technology calling")
    fleet.write("40-Treasury/durable-financial-insight.md",
                KNOWLEDGE_TMPL.format(title="Durable financial insight", pillar="financial"))
    r = fleet.run("vault-lint.py")
    assert r.returncode == EXIT_VIOLATION
    assert "LINT PILLARS" in r.stdout
    # the valid note must not be dragged in by the broken vocabulary
    assert "durable-financial-insight" not in r.stdout, r.stdout


def test_bank_rejects_sub3_target_before_writing(fleet):
    # ADR-0030: the executor must reject a floor violation at PRE-FLIGHT. The commit gate now
    # enforces the floor too, so a sub-3 stem that slipped past pre-flight would be written to
    # Treasury and *then* blocked at commit — stranding the executor half-applied.
    make_proposal(fleet, "shortname", **good_create(target="40-Treasury/short-note.md"))
    fleet.setup_commit("queue sub-3 proposal")
    r = fleet.run("vault-refine-execute.py")
    assert r.returncode == EXIT_VIOLATION, r.stdout + r.stderr
    assert "hyphen-tokens" in r.stdout, r.stdout
    assert not fleet.exists("40-Treasury/short-note.md")   # no Treasury write


def test_multiword_pillar_is_one_kebab_token(fleet):
    # `mental-health` is ONE pillar. The proof is the subset check: were it parsed as two
    # tokens (`mental`, `health`), {mental-health} would not be a subset and the note below
    # would fail. Passing therefore proves single-token parsing, not merely a clean lint.
    pin_pillars(fleet, "mental-health financial social technology calling")
    fleet.write("40-Treasury/mental-health-sleep-insight.md",
                KNOWLEDGE_TMPL.format(title="Sleep insight", pillar="mental-health"))
    r = fleet.run("vault-lint.py")
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert "LINT PILLARS" not in r.stdout


def test_commit_gate_blocks_new_sub3_token_name(fleet):
    # ADR-0030: the floor is enforced at the gate for ADDED names.
    fleet.write("20-Claims/sample-claim.md", "# sample\n")
    fleet.git("add", "20-Claims/sample-claim.md")
    r = fleet.git("commit", "-m", "add a sub-3 claim")   # NOT --no-verify: the gate must fire
    assert r.returncode != 0, r.stdout + r.stderr
    assert "BLOCKED" in (r.stdout + r.stderr), r.stdout + r.stderr
    assert "hyphen-tokens" in (r.stdout + r.stderr), r.stdout + r.stderr


def test_commit_gate_allows_conforming_new_name(fleet):
    fleet.write("20-Claims/sample-conforming-claim.md", "# claim\n")
    fleet.git("add", "20-Claims/sample-conforming-claim.md")
    r = fleet.git("commit", "-m", "add a conforming claim")
    assert r.returncode == 0, r.stdout + r.stderr


def test_commit_gate_exempts_convention_names(fleet):
    # README.md / dailies / *.example are tool- or convention-mandated: the gate must not
    # apply the kebab/floor rule to them (RULES["exempt_names"] / ["exempt_globs"]).
    fleet.write("20-Claims/README.md", "# readme\n")
    # a date-stemmed file is 2 tokens, below the >=3 floor: the exemption must survive the
    # daily-close retirement (ADR-0032) because retained dailies stay under the commit gate
    fleet.write("10-Logbook/Daily/2026-07-17.md", "---\ntype: note\n---\n# 2026-07-17\n")
    fleet.git("add", "-A")
    r = fleet.git("commit", "-m", "add exempt names")
    assert r.returncode == 0, r.stdout + r.stderr


def test_commit_gate_grandfathers_existing_names(fleet):
    # --diff-filter=AR means the gate cannot fire on a name that was already committed.
    # This is why enforcement could switch on without a rename pass (ADR-0030).
    fleet.write("20-Claims/sample-claim.md", "# sample\n")
    fleet.setup_commit("pre-existing sub-3 name lands via --no-verify")
    (fleet.vault / "20-Claims" / "sample-claim.md").write_text("# sample\nedited\n")
    fleet.git("add", "20-Claims/sample-claim.md")
    r = fleet.git("commit", "-m", "modify the grandfathered file")   # M, not A/R
    assert r.returncode == 0, r.stdout + r.stderr


def test_space_bearing_pillar_is_inexpressible(fleet):
    # The complement of the test above, and the real protection ADR-0029 relies on:
    # whitespace ALWAYS separates, so "mental health" cannot name one pillar. It parses as
    # two (`mental`, `health`), and a note claiming the space-bearing name fails the subset
    # check. This is why the kebab rule needs no pillar->slug transform: the filename-hostile
    # value can never enter the vocabulary in the first place.
    pin_pillars(fleet, "mental health financial social technology calling")
    fleet.write("40-Treasury/spaced-pillar-claim.md",
                KNOWLEDGE_TMPL.format(title="Spaced pillar claim", pillar='"mental health"'))
    r = fleet.run("vault-lint.py")
    assert r.returncode == EXIT_VIOLATION
    assert "pillars must be non-empty subset" in r.stdout, r.stdout
    # and the vocabulary itself is well-formed — the fault is the note, not the config
    assert "LINT PILLARS" not in r.stdout, r.stdout
