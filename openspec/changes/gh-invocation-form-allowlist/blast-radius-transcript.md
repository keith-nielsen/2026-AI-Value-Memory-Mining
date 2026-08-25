<!-- SPDX-License-Identifier: Apache-2.0 -->
# Blast radius transcript — G0

Measured 2026-08-25T21:0x+08:00 against `change/gh-invocation-form-allowlist` rebased onto
`main` @ `origin/main`. Commands and output, not a composed summary (ADR-0031 / this change's
own G0.1 instruction).

---

## G0.1 — every `gh` occurrence, partitioned

```
grep -rn --include='*.py' --include='*.sh' --include='*.yml' --include='*.md' \
     -E '(^|[^a-zA-Z_-])gh ' \
     tools/ tests/ .github/ docs/ openspec/ vault-template/ README.md AGENTS.md CONTRIBUTING.md \
  | awk -F: '{print $1}' | sort | uniq -c | sort -rn
```

```
     39 openspec/changes/gh-invocation-form-allowlist/tasks.md
     29 openspec/changes/gh-invocation-form-allowlist/proposal.md
     28 tests/test_pr_flow.py
     20 tests/test_gh_invocation_guard.py
     19 vault-template/99-Operations/scripts/gh-invocation-guard-script.md
     18 tools/pr-flow.py
     16 openspec/changes/gh-invocation-form-allowlist/blast-radius-transcript.md
     12 tools/ship-release.py
     12 tools/pr-state.py
     12 openspec/adr/0045-gh-invocation-form-allowlist.md
     10 openspec/specs/maintenance/spec.md
      9 tests/test_ceremony_tools.py
      9 tests/test_capability_vocabulary.py
      7 openspec/changes/archive/2026-07-14-release-object-per-tag/proposal.md
      6 openspec/changes/archive/2026-08-17-probe-vocabulary-and-json/proposal.md
      6 openspec/changes/archive/2026-08-04-add-pr-flow-driver/proposal.md
      5 openspec/changes/archive/2026-07-14-release-object-per-tag/specs/maintenance/spec.md
      5 openspec/changes/archive/2026-07-14-release-object-per-tag/design.md
      4 tools/gh_read.py
      4 openspec/changes/archive/2026-07-18-add-ship-ceremony-tools/proposal.md
      4 openspec/adr/0027-release-object-per-tag-and-guard-conformance.md
      4 AGENTS.md
      3 vault-template/99-Operations/scripts/outbound-publish-guard-script.md
      3 tests/test_emitted_command_shape.py
      3 openspec/specs/access-control/spec.md
      3 openspec/changes/gh-invocation-form-allowlist/specs/access-control/spec.md
      3 openspec/changes/archive/2026-08-24-seed-auto-memory-store/tasks.md
      3 openspec/changes/archive/2026-07-18-add-ship-ceremony-tools/specs/maintenance/spec.md
      3 openspec/changes/archive/2026-07-14-release-object-per-tag/specs/access-control/spec.md
      3 .github/workflows/openspec-canary.yml
      3 CONTRIBUTING.md
      2 tests/test_inv6_offline.py
      2 openspec/changes/archive/2026-08-16-estate-scoped-capability-probe/proposal.md
      2 openspec/changes/archive/2026-07-19-fix-operator-only-path-diagnostics/tasks.md
      2 openspec/changes/archive/2026-07-18-require-transcript-verification/tasks.md
      2 openspec/changes/archive/2026-07-18-add-ship-ceremony-tools/tasks.md
      2 openspec/changes/archive/2026-07-17-retire-effort-projections/tasks.md
      2 openspec/changes/archive/2026-07-14-release-object-per-tag/tasks.md
      2 openspec/adr/0034-branch-and-tag-rulesets.md
      1 vault-template/.claude/hooks/outbound-publish-guard.py
      1 vault-template/96-Runbooks/session-bootstrap-loader.md
      1 tools/inv6-offline-check.py
      1 tests/test_secret_scan.py
      1 README.md
      1 openspec/changes/gh-invocation-form-allowlist/specs/maintenance/spec.md
      1 openspec/changes/archive/2026-08-25-document-venv-path-shadowing/tasks.md
      1 openspec/changes/archive/2026-08-18-relocate-fleet-in-tree-bin/tasks.md
      1 openspec/changes/archive/2026-08-18-add-fleet-inventory-conformance/tasks.md
      1 openspec/changes/archive/2026-08-17-probe-vocabulary-and-json/tasks.md
      1 openspec/changes/archive/2026-08-17-emission-record-downgrades-ask/proposal.md
      1 openspec/changes/archive/2026-08-16-constitutional-diff-gate/tasks.md
      1 openspec/changes/archive/2026-08-06-flip-scope-review-blocking/tasks.md
      1 openspec/changes/archive/2026-08-04-add-pr-flow-driver/tasks.md
      1 openspec/changes/archive/2026-08-04-add-pr-flow-driver/specs/maintenance/spec.md
      1 openspec/changes/archive/2026-07-28-enforce-inv6-offline-check/specs/maintenance/spec.md
      1 openspec/changes/archive/2026-07-28-enforce-inv6-offline-check/proposal.md
      1 openspec/changes/archive/2026-07-17-enforce-pillar-slug-tokens/tasks.md
      1 openspec/changes/archive/2026-07-17-enforce-naming-token-floor/tasks.md
      1 openspec/adr/0038-complete-required-status-checks.md
      1 docs/USING-THIS-TEMPLATE.md
```

⚠ **This output was TRUNCATED when first recorded, and G5.1's re-run diff is what found it.**
The original block ended after 30 lines, at the point where per-file counts drop to
`2` — a `head`-shaped cut, not a filter. The full sweep returns **60** lines. Gate 1 requires the
*full, untruncated* output precisely so a Gate 4 re-run can diff against it; a truncated record
cannot distinguish a NEW match from one that was always there and simply went unrecorded.

**No live caller was hidden by it — verified, not assumed.** Every file revealed by the untruncated
sweep was checked against `git diff --name-only main...HEAD`: this branch touches **nothing** under
`openspec/changes/archive/`, `docs/`, `openspec/adr/0034`, `openspec/adr/0038`,
`tools/inv6-offline-check.py`, `tests/test_secret_scan.py`, `vault-template/96-Runbooks/` or
`vault-template/.claude/hooks/`. They therefore matched when G0.1 was first run and were simply cut
off. Each was then read: all are prose, docstrings, test strings or documentation tables —
**none executes `gh`**. The LIVE partition below is unchanged at five surfaces.

### Partition

**LIVE — executes `gh`:** `tools/gh_read.py`, `tools/pr-state.py`, `tools/pr-flow.py`,
`tools/ship-release.py`, `.github/workflows/openspec-canary.yml`.

**FROZEN — record only, never executed:** everything under `openspec/changes/archive/`, the ADRs,
the capability specs, `AGENTS.md`, `CONTRIBUTING.md`, `docs/`, and this change's own
`proposal.md` / `tasks.md`. These are text *about* `gh` forms. A matcher must never treat them as
callable, and no control in this change reads them.

**TEST — asserts on `gh` strings without executing them:** `tests/test_pr_flow.py` (28),
`tests/test_ceremony_tools.py` (9), `tests/test_capability_vocabulary.py` (9),
`tests/test_emitted_command_shape.py` (3), `tests/test_inv6_offline.py` (2). These assert on
*emitted command text*; INV-6 forbids the suite from reaching the network.

---

## G0.2 — the fleet's `gh` consumers, partitioned by whether the hook can see them

```
grep -nE '"gh"|\[.gh.,|gh api|gh auth|gh pr|gh run|gh release' \
     tools/gh_read.py tools/pr-flow.py tools/ship-release.py tools/pr-state.py
```

Call sites that actually execute (`_run([...])` / `run([...])` with a list argv):

| File | Line | argv | Allowlist verdict |
|---|---|---|---|
| `tools/gh_read.py` | 112 | `["gh", "api", path]` | **permitted** (`gh api`) |
| `tools/pr-flow.py` | 1419 | `["gh", "auth", "status"]` | **permitted** (`gh auth status`) |
| `tools/pr-state.py` | 83 | `["gh", "pr", "view", number, "--json", …]` | **would be REFUSED** |
| `tools/pr-state.py` | 168 | `["gh", "run", "list", "--commit", …]` | **would be REFUSED** |

`tools/ship-release.py` no longer shells out to `gh release view` / `gh release list` — item 21
moved it onto `gh_read`; its remaining `gh` mentions are prose and emitted-command text.

### The asymmetry this change's spec MUST state

**A `PreToolUse` Bash hook sees only the command the agent types.** Every call site above is a
Python `subprocess` inside a tool. When the agent runs `python3 tools/pr-state.py …`, the hook is
handed `python3 tools/pr-state.py …` — it never sees `gh pr view`. The same is true of the
enumerated `permissions.deny` entries, which match on the Bash command string.

Consequences, stated rather than left to be discovered:

1. **`pr-state.py` will keep invoking `gh pr view` and `gh run list` after this change lands**, and
   neither layer will refuse them. That is not a defect to fix here; it is the boundary of what a
   Bash-command matcher can bind.
2. **The agent typing `gh pr view` is refused while a tool calling it is not.** A reader who does
   not know this will credit the control with coverage it does not have — the ADR's own
   *"a control that will be credited with more than it does"*.
3. **The refused forms already fail on their own merits in a confined session.** `gh pr view` uses
   GraphQL, which 401s unconditionally when `gh credential` measures `UNAUTHENTICATED`;
   `pr-state.py` handles that by design — line 86 sets `graphql = False` and degrades to anonymous
   REST via `gh_read`, and the `gh run list` path at 168 is gated on `graphql` being true, so it is
   unreachable in that state. **Landing the allowlist therefore breaks no live caller.**

### A third surface neither layer reaches

```
.github/workflows/openspec-canary.yml:49:  gh label create openspec-canary --color b60205 \
.github/workflows/openspec-canary.yml:51:  open=$(gh issue list --label openspec-canary --state open --json number --jq 'length')
.github/workflows/openspec-canary.yml:55:  gh issue create \
```

These run on GitHub-hosted runners with an Actions token. There is no Claude Code harness there, so
**no hook and no `permissions` block applies to them at all** — `gh label create`, `gh issue list`
and `gh issue create` are all forms the allowlist would refuse locally and cannot touch in CI. The
spec should not imply otherwise.

---

## G0.3 — pre-change baseline of the three `settings.json`

⚠ **This block previously carried a PSEUDOCODE description in place of a command**
(`for each of USER / VAULT / FRAMEWORK settings.json: keys, len(...)`). Its output was real, but
Gate 1 requires *"the exact search command(s) plus their full, untruncated output"*, and **G5.1 is
"re-run the G0 sweeps; diff output against this transcript"** — which was not performable for G0.3.
The exact command is restored below. Both runs are kept, because this row is a *pre-change baseline*
and therefore cannot reproduce after the change lands; the diff between them is this change's own
footprint, which is what G5.1 should expect to see.

The command (re-runnable; requires `config.env` sourced for the two root variables):

```
python3 - "$HOME/.claude/settings.json" \
         "$VAULT_ROOT/.claude/settings.json" \
         "$FRAMEWORK_ROOT/.claude/settings.json" <<'PY'
import json, sys
for label, path in zip(("USER", "VAULT", "FRAMEWORK"), sys.argv[1:]):
    d = json.load(open(path))
    blocks = d.get("hooks", {}).get("PreToolUse", [])
    hooks = sum(len(b.get("hooks", [])) for b in blocks)
    deny = d.get("permissions", {}).get("deny", [])
    print(f"  {label:10} keys={sorted(d)}")
    print(f"  {'':10} PreToolUse-blocks={len(blocks)}  hooks-within={hooks}  permissions.deny={len(deny)}")
PY
```

**PRE-CHANGE baseline, 2026-08-25** (as originally recorded; `keys` in file order, and counting
matcher-blocks only):

```
  USER       keys=['permissions','model','effortLevel','tui','enabledPlugins','autoMode']
             PreToolUse-blocks=0   permissions.deny=0
  VAULT      keys=['permissions','sandbox','hooks']
             PreToolUse-blocks=1   permissions.deny=10
  FRAMEWORK  keys=['hooks']
             PreToolUse-blocks=1   permissions.deny=0
```

**POST-CHANGE re-run at `eb14905`, 2026-08-26** (`keys` sorted by the command above):

```
  USER       keys=['autoMode', 'effortLevel', 'enabledPlugins', 'model', 'permissions', 'tui']
             PreToolUse-blocks=0  hooks-within=0  permissions.deny=0
  VAULT      keys=['hooks', 'permissions', 'sandbox']
             PreToolUse-blocks=1  hooks-within=1  permissions.deny=10
  FRAMEWORK  keys=['hooks', 'permissions']
             PreToolUse-blocks=1  hooks-within=2  permissions.deny=5
```

**The delta is exactly this change, and nothing else:** FRAMEWORK gains a `permissions` key,
`permissions.deny` 0 -> 5, and `hooks-within` 1 -> 2. USER and VAULT are byte-for-byte unchanged in
every counted field. ⚠ **Unit note, added because the two rows are easy to read as contradictory:**
G0.3 counts `PreToolUse` **matcher-blocks** (1 both before and after), while G3.5's evidence records
"Bash hooks 1 -> 2" — the **hooks *within*** that single block. Both are true; they count different
things. `hooks-within` is emitted above so the two rows can be diffed without reconciling units by
hand.

Paths, root-prefixed to avoid the overloaded-basename trap:

- USER — `$HOME/.claude/settings.json`
- VAULT — `$VAULT_ROOT/.claude/settings.json`
- FRAMEWORK — `$FRAMEWORK_ROOT/.claude/settings.json`

**Red confirmed, as the ADR asserted:** `$FRAMEWORK_ROOT/.claude/settings.json` has **no
`permissions` block at all** — its only top-level key is `hooks`. The five Layer-1 deny entries
exist in the VAULT (within its 10) and, on this branch only, in `vault-template/`. G3.5's
"Red first" condition is therefore satisfied by this baseline.

USER carries no `PreToolUse` hooks and no deny entries, which is also what made the G1.1 lab
measurement uncontaminated — user settings merge into every session.
