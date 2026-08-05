<!-- SPDX-License-Identifier: Apache-2.0 -->

# Change: bootstrap-capability-probe

## Why

The cold-start prime loads **context** but never measures **capability**. These differ in kind:
context is corpus (stable, re-readable); capability is *environment state* — write scope, credential
visibility, network reach — which changes between sessions with **no event the agent can observe**.

Attested 2026-08-05 (banked as **F35**). Asked to edit a repo outside the sandbox write scope, the
agent asserted *"no network to fetch or push"* from a single `git fetch` failure whose text was
`unable to get credential storage lock in 1000 ms: Read-only file system` — a **write** error read as
a **network** verdict. In fact GitHub reads worked (`200`), and `git push` worked (`credential.helper=store`,
a different channel from `gh`'s keyring); only `gh` *mutations* were unavailable. The agent then built
an unnecessary verification ritual for the operator on that false premise and retracted it twice.

**Three instruments already held the answer and none bound the session:**

| Instrument | Said | Why it did not fire |
|---|---|---|
| memory `inv14-egress-investigation-state` | "the only barrier to non-push egress is credential absence" | in context from the first token; never applied |
| `maintenance` — *Platform Capability Is Probed, Not Recalled* (PR #51) | ownership "SHALL NOT be asserted … from recollection, because … a stored answer preserves a wrong one" | binds the **driver's code**; nothing bound the agent's own assertions |
| `tools/pr-flow.py --capabilities` | prints the whole matrix in one call | **never run** — four worse probes were hand-rolled instead |

The gap is therefore narrow and specific: **the existing criterion is correct and unowned by the
session.** This change binds it, and imports rather than restates it.

## Nature of the change — ordinary, not a constitution-override

Derived from the enforcing artifacts, not paraphrased:

- `maintenance/spec.md` carries `protects: [INV-2, INV-3, INV-6]` (Tier 0).
- `constitution.md` §3 governs an **override** of a Tier-0/Tier-1 element. This change **ADDS** a
  requirement; it does not modify, weaken, or narrow INV-2, INV-3, INV-6, or any existing requirement.
  Nothing is sacrificed, so there is no override and no Gate-4 sacrifice to accept.
- Therefore: **ordinary OpenSpec change**, with a full blast-radius sweep and regression recorded below.

**Finding raised separately (not addressed here):** `constitution.md` §4 states `constitution-lint`
*"fails if a diff touches a `protects:`-tagged element without a complete `constitution-override`."*
The job (`.github/workflows/ci.yml:33–80`) performs **no diff analysis** — it checks only that the six
specs still contain a `protects:` string, that `constitution.md` still contains `CONST-01`–`05`, and
that the override template file exists. The documented gate is a paraphrase of a weaker mechanism
(class 9) and a declared enforcement end-state never reconciled (class 8). **CI green is not evidence
of ceremony compliance.** Belongs in the GitHub-platform-hardening queue.

## What Changes

- **ADDED requirement** (`maintenance`): *The Session Prime Measures Capability Before Asserting It* —
  probe before claiming; four independent layers, none inferred from another; reference the existing
  reporter rather than restate it; capability ≠ authority (INV-14). Four scenarios.
- **MODIFIED runbook** `vault-template/96-Runbooks/session-bootstrap-loader.md` — fifth gate
  **measure-don't-infer**; new step 3 **Capability probe**; steps renumbered 3→4, 4→5; Purpose,
  Pitfalls, Verification, `trigger`, `last-validated` updated.
- **MODIFIED adapters, in lockstep** — both enumerate the gates by name and would otherwise drift to a
  stale count: `vault-template/CLAUDE.md`, `vault-template/.claude/commands/vmm-session-rebooted.md`.

**Design constraint honoured:** the runbook **references** the capability reporter and states the four
layers; it does **not** inline `gh`/`curl` commands or read a harness-specific settings path. An earlier
draft did both, violating the *Runbook Format* requirement it must satisfy ("Deterministic steps MUST
reference meta-scripts rather than restate them"; "no tool-specific invocation as its source of truth").
Caught by this change's own blast-radius sweep. Concrete invocations live in the adapters, where
harness specifics belong.

## Blast radius (swept, re-runnable)

```
grep -rn 'session-bootstrap-loader' openspec/ vault-template/ docs/ .github/ README.md AGENTS.md CONTRIBUTING.md CLAUDE.md
grep -rn 'governance-first\|four gates\|the gates' vault-template/CLAUDE.md vault-template/.claude/commands/vmm-session-rebooted.md AGENTS.md CLAUDE.md
```

| Reference | Action |
|---|---|
| `vault-template/CLAUDE.md:4` | **UPDATED** — enumerated four gates by name |
| `vault-template/.claude/commands/vmm-session-rebooted.md:9` | **UPDATED** — said "the four gates" |
| `AGENTS.md:130` | **no change** — says "engage the gates", count-agnostic |
| `vault-template/.claude/settings.json:43` | **no change** — `cat`s the runbook, content-agnostic |
| `openspec/adr/0017`, `0032`; 6 archived changes | **no change** — historical records, correctly immutable |

## Regression evidence

| Check | Result |
|---|---|
| `runbook-lint` (CI job reproduced locally) | **4 runbooks checked, 0 errors, exit 0** |
| `openspec validate --all --strict` | **7 passed, 0 failed, exit 0** (CLI `1.6.0` == `package.json` pin) |
| `vault-template/.claude/settings.json` | valid JSON (unchanged) |
| `validate-scripts.sh` | no `.py` touched — expected no-op |

## Impact

No `.py` changes; no schema changes; no existing requirement modified; no script behaviour changed.

**Named residual:** the capability reporter is `tools/pr-flow.py --capabilities`, a **framework-repo**
tool. A vault deployed without the repo alongside it has no reporter, and INV-6 forbids the
deterministic vault fleet from making the network calls two of the four layers require. The runbook is
written to reference the reporter the adapter names, so this degrades to the harness adapter — it is
**not solved here** and is recorded rather than papered over.

**Deploy-down:** live `96-Runbooks/session-bootstrap-loader.md`, `CLAUDE.md`, and
`.claude/commands/vmm-session-rebooted.md` are deployed copies inside `denyWrite` — operator-applied,
never edited in-vault.
