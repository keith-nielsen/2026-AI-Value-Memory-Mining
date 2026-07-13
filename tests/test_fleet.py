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

DAILY_TMPL = """---
type: daily
date: {day}
closed:
---
# {day}

## Log
Work happened.

## Captured
- Idea: something worth a claim later.
"""


def make_day(fleet, day):
    fleet.write(f"10-Logbook/Daily/{day}.md", DAILY_TMPL.format(day=day))


def make_proposal(fleet, name, **fields):
    fleet.write(f"20-Claims/_refine-approved/{name}.json", json.dumps(fields, indent=2))


def good_create(target="40-Treasury/good-insight.md", **over):
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
# close-day lifecycle + gates
# --------------------------------------------------------------------------------------

def test_close_strict_order_gate(fleet):
    make_day(fleet, "2020-01-01")
    make_day(fleet, "2020-01-02")
    fleet.setup_commit("two open days")
    r = fleet.run("vault-close-day.py", "2020-01-02")
    assert r.returncode == EXIT_BLOCKED
    assert "BLOCKED" in (r.stdout + r.stderr)
    # the later day must not have been sealed
    assert "closed: 2" not in fleet.read("10-Logbook/Daily/2020-01-02.md")


def test_close_seals_and_lints(fleet):
    make_day(fleet, "2020-01-01")
    fleet.setup_commit("one open day")
    r = fleet.run("vault-close-day.py", "2020-01-01")
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    sealed = fleet.read("10-Logbook/Daily/2020-01-01.md")
    assert "## Close" in sealed
    assert "closed: 2" in sealed  # closed: set to a real date
    check = fleet.run("vault-close-day.py", "--check", "2020-01-01")
    assert check.returncode == EXIT_OK
    assert "close-lint OK" in check.stdout


def test_close_commit_is_scoped_not_a_sweep(fleet):
    make_day(fleet, "2020-01-01")
    fleet.setup_commit("one open day")
    # unrelated, uncommitted working-tree content that a close must NOT sweep
    fleet.write("30-Sites/unrelated-dirty-note.md", "dirty working copy\n")
    fleet.run("vault-close-day.py", "2020-01-01")
    assert fleet.head_message().startswith("close: 2020-01-01 daily")
    files = fleet.head_files()
    assert files == ["10-Logbook/Daily/2020-01-01.md"], files
    # the unrelated file is still uncommitted (untracked), left untouched by the close
    porcelain = fleet.git("status", "--porcelain").stdout
    assert "30-Sites/unrelated-dirty-note.md" in porcelain


def test_close_missing_note_blocks(fleet):
    r = fleet.run("vault-close-day.py", "2019-12-31")
    assert r.returncode == EXIT_BLOCKED
    assert "no daily note" in (r.stdout + r.stderr)


# --------------------------------------------------------------------------------------
# daily-note: unconditional create, own commit, idempotent no-op
# --------------------------------------------------------------------------------------

def test_daily_note_owns_its_commit_and_is_idempotent(fleet):
    before = fleet.commit_count()
    r1 = fleet.run("vault-daily-note.py")
    assert r1.returncode == EXIT_OK, r1.stdout + r1.stderr
    assert "created" in r1.stdout
    assert fleet.commit_count() == before + 1
    assert fleet.head_message().startswith("daily: opened ")
    # second run is a pure no-op: no new commit (INV-2), reports "exists"
    r2 = fleet.run("vault-daily-note.py")
    assert r2.returncode == EXIT_OK
    assert "exists" in r2.stdout
    assert fleet.commit_count() == before + 1


# --------------------------------------------------------------------------------------
# refine executor: whole-proposal pre-flight, no partial writes, batch isolation
# --------------------------------------------------------------------------------------

def test_bank_applies_conforming_proposal_atomically(fleet):
    make_proposal(fleet, "a-good", **good_create())
    fleet.setup_commit("queue proposal")
    r = fleet.run("vault-refine-execute.py")
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert fleet.exists("40-Treasury/good-insight.md")
    note = fleet.read("40-Treasury/good-insight.md")
    assert "grade: gold" in note
    assert fleet.head_message() == "bank: good-insight"
    # one atomic commit: the note, its Catalog index, and the consumed proposal (a deletion)
    files = set(fleet.head_files())
    assert "40-Treasury/good-insight.md" in files
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
    fleet.write("40-Treasury/existing-note.md", "PRECIOUS existing content\n")
    make_proposal(fleet, "collide", **good_create(target="40-Treasury/existing-note.md"))
    fleet.setup_commit("existing + colliding proposal")
    r = fleet.run("vault-refine-execute.py")
    assert r.returncode == EXIT_VIOLATION
    assert "INV-9" in r.stdout
    # the existing note is untouched — no partial write clobbered it
    assert fleet.read("40-Treasury/existing-note.md") == "PRECIOUS existing content\n"


def test_bank_rejects_missing_index_link_before_writing(fleet):
    make_proposal(fleet, "dangling", **good_create(
        index_links=["40-Treasury/Catalog/does-not-exist-index.md"]))
    fleet.setup_commit("proposal with dangling link")
    r = fleet.run("vault-refine-execute.py")
    assert r.returncode == EXIT_VIOLATION
    assert "index link target missing" in r.stdout
    # pre-flight rejects the whole proposal — the note is never written
    assert not fleet.exists("40-Treasury/good-insight.md")


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
    assert fleet.exists("40-Treasury/good-insight.md")
    # linked into the holding queue, not orphaned
    assert "[[good-insight]]" in fleet.read("40-Treasury/Catalog/pending-catalog-index.md")
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
    note = "99-Operations/scripts/daily-note-script.md"
    fleet.write(note, fleet.read(note) + "\n```python\nprint('stowaway second fence')\n```\n")
    r = fleet.run("vault-render.py", "reconcile")
    assert r.returncode == EXIT_VIOLATION
    assert "VIOLATION" in r.stdout
    assert "daily-note-script.md" in r.stdout


# --------------------------------------------------------------------------------------
# env-free root resolution (ADR-0023): cwd marker-walk vs. no-vault BLOCKED
# --------------------------------------------------------------------------------------

def test_bare_run_resolves_root_from_cwd(fleet):
    # no VAULT_ROOT in the environment — resolution must walk up from cwd to the marker
    r = fleet.run("vault-daily-note.py", vault_root=False, cwd=fleet.vault)
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert "created" in r.stdout


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
    r = fleet.run(script, slug)
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert not fleet.exists(f"30-Sites/{slug}")
    assert fleet.exists(f"{dest}/{slug}/sample-effort-site.md")
    assert fleet.head_message().startswith(f"{verb}:")


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
