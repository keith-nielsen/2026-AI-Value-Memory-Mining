"""The linter refuses a working-memory store path that does not resolve inside the vault.

The framework ships `.claude/settings.local.json.example` carrying a placeholder path. A
placeholder is a comment asking an installer to act, and `CONTRIBUTING.md:92` is this
repository's standing finding that a rule which cannot refuse does not bind — so the seed
travels with the check that refuses it, and this file is what holds that check honest.

The case that motivated choosing a check over an install-time prompt is the ESCAPE case: a
declared path resolving OUTSIDE the vault root works perfectly. Nothing fails, nothing warns,
and one deployment's memory silently merges with another's or with a user-global store. A
placeholder-string comparison would not see it; a resolution test does.

METHOD — the tests execute the SHIPPED text.

    The guard is sliced out of `knowledge-lint-script.md` at import time and `exec`'d. It is
    not reimplemented here. A test written against a copy of the logic passes while the
    deployed script diverges, which is precisely the vacuous-coverage failure this suite has
    been bitten by before.

STATED LIMIT — read before trusting this file:

    These tests establish that the guard classifies paths correctly. They do NOT establish
    that the guard RUNS in a deployed vault: that depends on `render` having deployed the
    note to `99-Operations/bin/vault-lint.py`, which is an operator step outside pytest's
    reach. Rendering drift is `reconcile`'s job, not this file's.
"""
import json
import pathlib
import shutil
import tempfile

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
NOTE = REPO / "vault-template" / "99-Operations" / "scripts" / "knowledge-lint-script.md"

START = "# --- harness working-memory store"
END = "# All other content file stems."


def _guard_source() -> str:
    src = NOTE.read_text(encoding="utf-8")
    assert START in src, f"guard block missing from {NOTE.name} — it is the subject of this file"
    assert END in src, f"anchor {END!r} missing from {NOTE.name}"
    block = src[src.index(START) : src.index(END)]
    assert "autoMemoryDirectory" in block
    return block


GUARD = _guard_source()


def _run(setup):
    """Execute the shipped guard against a throwaway vault; return (store, [messages])."""
    root = pathlib.Path(tempfile.mkdtemp(prefix="vault-fixture-"))
    try:
        (root / ".claude").mkdir()
        setup(root)
        ns = {"json": json, "pathlib": pathlib, "vault": root, "violations": []}
        exec(GUARD, ns)  # noqa: S102 — executing the shipped source is the point
        return ns["store"], [msg for _, msg in ns["violations"]]
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _declare(root: pathlib.Path, value: str) -> None:
    (root / ".claude" / "settings.local.json").write_text(
        json.dumps({"autoMemoryDirectory": value}), encoding="utf-8"
    )


# --- refusing cases first: a guard is only interesting where it says no -------------------

def test_placeholder_shipped_verbatim_is_refused():
    """The exact string the seed ships. This is the whole reason the guard exists."""
    placeholder = "/ABSOLUTE/PATH/TO/YOUR/Vault/10-Logbook/vmm-working-memory"
    store, msgs = _run(lambda r: _declare(r, placeholder))
    assert store is None
    assert any("does not exist" in m and placeholder in m for m in msgs)


def test_declared_path_is_a_file_is_refused_distinctly():
    def setup(r):
        (r / "10-Logbook").mkdir()
        (r / "10-Logbook" / "store").write_text("not a directory", encoding="utf-8")
        _declare(r, str(r / "10-Logbook" / "store"))

    store, msgs = _run(setup)
    assert store is None
    assert any("is not a directory" in m for m in msgs)
    assert not any("does not exist" in m for m in msgs), "distinct cases, distinct remedies"


def test_symlink_escaping_the_vault_is_refused():
    """Resolution happens BEFORE containment — the case a `startswith` check waves through."""
    outside = pathlib.Path(tempfile.mkdtemp(prefix="other-vault-"))

    def setup(r):
        (r / "10-Logbook").mkdir()
        (r / "10-Logbook" / "vmm-working-memory").symlink_to(outside)
        _declare(r, str(r / "10-Logbook" / "vmm-working-memory"))

    try:
        store, msgs = _run(setup)
        assert store is None
        assert any("resolves outside the vault" in m for m in msgs)
    finally:
        shutil.rmtree(outside, ignore_errors=True)


def test_relative_path_is_refused():
    store, msgs = _run(lambda r: _declare(r, "10-Logbook/vmm-working-memory"))
    assert store is None
    assert any("not an absolute path" in m for m in msgs)


def test_malformed_settings_file_is_refused_not_ignored():
    """A settings file that cannot be parsed must not read as 'no store declared'."""
    store, msgs = _run(
        lambda r: (r / ".claude" / "settings.local.json").write_text("{nope", encoding="utf-8")
    )
    assert store is None
    assert any("not readable JSON" in m for m in msgs)


# --- passing cases: the store is optional, and its contents are not ours ------------------

def test_correctly_configured_store_passes():
    def setup(r):
        (r / "10-Logbook" / "vmm-working-memory").mkdir(parents=True)
        _declare(r, str(r / "10-Logbook" / "vmm-working-memory"))

    store, msgs = _run(setup)
    assert store is not None
    assert msgs == []


@pytest.mark.parametrize(
    "setup",
    [
        pytest.param(lambda r: None, id="no-settings-file"),
        pytest.param(
            lambda r: (r / ".claude" / "settings.local.json").write_text(
                '{"sandbox": {"enabled": true}}', encoding="utf-8"
            ),
            id="no-declaration",
        ),
    ],
)
def test_absent_store_is_conformant(setup):
    """The store is optional. A check that demanded it would invent a requirement."""
    store, msgs = _run(setup)
    assert store is None
    assert msgs == []


def test_guard_reports_the_declared_path_verbatim():
    """Evidence, never a verdict string (F20) — a refusal must be actionable without re-deriving it."""
    declared = "/nonexistent/path/that/tells/the/operator/what/to/fix"
    _, msgs = _run(lambda r: _declare(r, declared))
    assert any(declared in m for m in msgs)
