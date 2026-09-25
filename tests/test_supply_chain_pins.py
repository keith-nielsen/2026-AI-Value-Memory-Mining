# SPDX-License-Identifier: Apache-2.0
"""Supply-chain inputs are pinned immutably and adopted after a cooldown (supply-chain-pin-and-cooldown).

Two properties, each of which drifts back silently if nothing checks it:

1. **Every GitHub Action is pinned to a full commit SHA, with its version in a trailing comment.**
   A tag such as `@v7` is a moving pointer: the tj-actions compromise (CVE-2025-30066) re-pointed
   existing tags, so every workflow referencing them ran the attacker's code at its next run. A
   40-hex commit SHA cannot be re-pointed. The `# vX.Y.Z` comment is what lets Dependabot keep the
   pin current and lets a reviewer read it; a pin without it is unmaintainable, so it is required.
   Local actions (`./…`) are exempt — they are this repository's own code at the checked-out commit.

2. **Every Dependabot ecosystem declares its cooldown explicitly**, at the value the policy sets:
   14 days for npm, 7 for everything else. GitHub applies a 3-day default when none is declared
   (2026-07-14), so an absent block is not "no cooldown" — it is a policy owned by someone else that
   can change without an event in this repository. Declared here, it is reviewable and tested.

Deliberately stdlib-only and line-based: a YAML parser discards comments, and the version comment is
half of what property 1 checks. Offline and deterministic (INV-6).
"""
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = sorted((REPO / ".github" / "workflows").glob("*.y*ml"))
DEPENDABOT = REPO / ".github" / "dependabot.yml"

USES = re.compile(r"^\s*-?\s*uses:\s*(?P<ref>[^\s#]+)\s*(?P<comment>#.*)?$")
PINNED = re.compile(r"^[\w.-]+/[\w.-]+(?:/[\w./-]+)?@[0-9a-f]{40}$")
VERSION_COMMENT = re.compile(r"^#\s*v\d+\.\d+\.\d+\b")

# The policy. Changing a value here is changing the policy, and belongs in a governed change.
COOLDOWN_DAYS = {"npm": 14}
COOLDOWN_DEFAULT = 7


def _uses_lines():
    for wf in WORKFLOWS:
        for n, line in enumerate(wf.read_text(encoding="utf-8").splitlines(), 1):
            m = USES.match(line)
            if m:
                yield wf.name, n, m.group("ref"), (m.group("comment") or "").strip()


def test_the_workflow_scan_is_not_vacuous():
    """A scan that finds nothing passes every assertion below. Prove it found the real surface."""
    assert WORKFLOWS, "no workflow files found — the pin check would pass vacuously"
    assert len(list(_uses_lines())) >= 20, "fewer `uses:` lines than the repo is known to carry"


def test_every_action_is_pinned_to_a_full_commit_sha():
    bad = [f"{wf}:{n}: {ref}" for wf, n, ref, _ in _uses_lines()
           if not ref.startswith("./") and not PINNED.match(ref)]
    assert not bad, ("actions referenced by a mutable ref (tag or branch) instead of a 40-hex commit "
                     "SHA — a tag can be re-pointed under you (tj-actions, CVE-2025-30066):\n  "
                     + "\n  ".join(bad))


def test_every_sha_pin_names_its_version():
    bad = [f"{wf}:{n}: {ref} {c!r}" for wf, n, ref, c in _uses_lines()
           if PINNED.match(ref) and not VERSION_COMMENT.match(c)]
    assert not bad, ("SHA pins without a trailing `# vX.Y.Z` comment — Dependabot cannot maintain "
                     "them and a reviewer cannot read them:\n  " + "\n  ".join(bad))


def _ecosystem_cooldowns(text):
    """{ecosystem: default-days or None} from dependabot.yml, by block. Line-based on purpose."""
    out, current = {}, None
    for line in text.splitlines():
        m = re.match(r"^\s*-\s*package-ecosystem:\s*['\"]?([\w-]+)['\"]?", line)
        if m:
            current = m.group(1)
            out[current] = None
            continue
        m = re.match(r"^\s*default-days:\s*(\d+)\s*(#.*)?$", line)
        if m and current:
            out[current] = int(m.group(1))
    return out


def test_every_dependabot_ecosystem_declares_its_cooldown():
    cooldowns = _ecosystem_cooldowns(DEPENDABOT.read_text(encoding="utf-8"))
    assert cooldowns, "no package-ecosystem blocks parsed — the check would pass vacuously"
    wrong = {eco: days for eco, days in cooldowns.items()
             if days != COOLDOWN_DAYS.get(eco, COOLDOWN_DEFAULT)}
    assert not wrong, (f"cooldown missing or off-policy (want npm={COOLDOWN_DAYS['npm']}, others="
                       f"{COOLDOWN_DEFAULT}): {wrong}. An absent block silently inherits GitHub's "
                       "default, which this repository does not control.")


def test_the_cooldown_parser_reads_blocks_not_the_whole_file():
    """The adversarial case: one ecosystem's value must not satisfy another's."""
    sample = ("updates:\n"
              "  - package-ecosystem: \"npm\"\n    cooldown:\n      default-days: 14\n"
              "  - package-ecosystem: \"pip\"\n    schedule:\n      interval: monthly\n")
    assert _ecosystem_cooldowns(sample) == {"npm": 14, "pip": None}
