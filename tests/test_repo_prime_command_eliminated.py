# SPDX-License-Identifier: Apache-2.0
"""The repo-work prime (`/vmm-repo-github`) is eliminated, and nothing it carried is lost.

WHY THIS EXISTS
---------------
PR #115 added `/vmm-repo-github`: a stub under `vault-template/.claude/commands/` (LOCKSTEP, so every
vault received it) that loaded a card from one vault's `30-Sites/`. A 2026-09-26 audit mapped every
item the stub and card carried to a source of record: all but three were already held by
`CONTRIBUTING.md`, `AGENTS.md`, the bootstrap and conduct runbooks, or enforced by the guards and the
driver. Operator decision 2026-09-26: repo work stays in vault-rooted sessions; remove the command
completely and move what was not redundant into existing guidance:

- the pointer a vault-rooted session needs (it loads none of the repo's governance) — bootstrap
  step 5, a just-in-time pointer, gated on `FRAMEWORK_ROOT` being declared;
- two facts no source of record carried — `AGENTS.md` operating notes.

These tests hold both halves: the command cannot quietly return, and the migrated content cannot
quietly go.

STATED LIMIT: text and placement only. Whether an agent follows a pointer is not observable here.
"""
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]
NAME = "vmm-repo-github.md"
COMMAND_DIRS = (REPO / ".claude" / "commands", REPO / "vault-template" / ".claude" / "commands")
BOOT = REPO / "vault-template" / "96-Runbooks" / "session-bootstrap-loader.md"
AGENTS = REPO / "AGENTS.md"


def _step5(text: str) -> str:
    """Bootstrap step 5 only — from its heading line to the start of step 6."""
    m = re.search(r"^5\. .*?Know the just-in-time pointers.*?(?=^6\. )", text, re.S | re.M)
    assert m, "bootstrap step 5 (just-in-time pointers) not found"
    return m.group(0)


def test_command_exists_in_no_commands_dir():
    present = [str(d.relative_to(REPO) / NAME) for d in COMMAND_DIRS if (d / NAME).exists()]
    assert not present, f"the eliminated command is present: {present}"


def test_bootstrap_step5_points_repo_work_at_its_sources():
    step5 = _step5(BOOT.read_text(encoding="utf-8"))
    for needle in ("$FRAMEWORK_ROOT/AGENTS.md", "$FRAMEWORK_ROOT/CONTRIBUTING.md",
                   "$FRAMEWORK_ROOT/docs/version-control-legal-moves.md"):
        assert needle in step5, f"bootstrap step 5 does not name {needle}"


def test_agents_carries_the_facts_only_the_card_held():
    text = AGENTS.read_text(encoding="utf-8")
    assert "Dependabot PR bodies carry no scope block" in text
    assert "run `npm ci`" in text
