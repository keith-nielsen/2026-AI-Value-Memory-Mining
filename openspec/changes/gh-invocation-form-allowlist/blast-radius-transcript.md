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
     29 openspec/changes/gh-invocation-form-allowlist/proposal.md
     28 tests/test_pr_flow.py
     18 tools/pr-flow.py
     12 tools/ship-release.py
     12 tools/pr-state.py
     11 openspec/changes/gh-invocation-form-allowlist/tasks.md
     10 openspec/specs/maintenance/spec.md
      9 tests/test_ceremony_tools.py
      9 tests/test_capability_vocabulary.py
      8 openspec/adr/0045-gh-invocation-form-allowlist.md
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
```

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

```
for each of USER / VAULT / FRAMEWORK settings.json:
    keys, len(hooks.PreToolUse), len(permissions.deny)
```

```
  USER       keys=['permissions','model','effortLevel','tui','enabledPlugins','autoMode']
             PreToolUse-blocks=0   permissions.deny=0
  VAULT      keys=['permissions','sandbox','hooks']
             PreToolUse-blocks=1   permissions.deny=10
  FRAMEWORK  keys=['hooks']
             PreToolUse-blocks=1   permissions.deny=0
```

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
