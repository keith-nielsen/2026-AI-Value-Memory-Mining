# SPDX-License-Identifier: Apache-2.0
"""The repo-work prime (`/vmm-repo-github`) belongs to the FRAMEWORK repo, and depends on no vault.

WHY THIS EXISTS
---------------
The prime was added by PR #115 under `vault-template/.claude/commands/`, a LOCKSTEP prefix, so the
mirror deployed it into EVERY vault. Two decisions made after it contradict that placement:

- a deployed vault is standalone and depends on nothing in the framework repo (conduct rule 26), yet
  the prime pointed at `$FRAMEWORK_ROOT` and at a `30-Sites/` card no other vault has;
- development knowledge loads only in framework-rooted sessions (memory partition, 2026-09-16), so
  repo work starts from a session rooted HERE, where `CLAUDE.md` -> `AGENTS.md` load by themselves.

Operator decision 2026-09-26: move the prime to this repo's own `.claude/commands/`, with the stated
future intent of a full split in which the framework repo's GitHub work is independent of the vault.
These tests hold that boundary so the prime cannot drift back into the vault or re-acquire a vault
dependency.

STATED LIMIT: this checks placement and text. Whether a session actually invokes the prime is a
harness behaviour no test here can observe.
"""
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]
NAME = "vmm-repo-github.md"
ROOT_PRIME = REPO / ".claude" / "commands" / NAME
TEMPLATE_PRIME = REPO / "vault-template" / ".claude" / "commands" / NAME

# A reference to any of these makes the prime depend on a deployed vault or on the vault's own
# environment (`FRAMEWORK_ROOT` is declared by the vault's config.env; a framework-rooted session
# stands in the repo and needs no variable to find it).
VAULT_COUPLINGS = ("VAULT_ROOT", "FRAMEWORK_ROOT", "30-Sites", "10-Logbook")


def test_prime_lives_in_the_framework_root():
    assert ROOT_PRIME.is_file(), f"missing: {ROOT_PRIME.relative_to(REPO)}"


def test_prime_is_not_shipped_to_vaults():
    assert not TEMPLATE_PRIME.exists(), (
        f"{TEMPLATE_PRIME.relative_to(REPO)} is under a LOCKSTEP prefix, so the mirror would deploy "
        "the repo-work prime into every vault")


def test_prime_carries_no_vault_coupling():
    text = ROOT_PRIME.read_text(encoding="utf-8")
    found = [c for c in VAULT_COUPLINGS if c in text]
    assert not found, f"the prime references vault-side names: {found}"


def test_prime_points_at_the_route_and_its_ssot():
    text = ROOT_PRIME.read_text(encoding="utf-8")
    for needle in ("tools/pr-flow.py --plan", "CONTRIBUTING.md", "AGENTS.md"):
        assert needle in text, f"the prime does not name {needle!r}"
