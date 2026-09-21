<!-- SPDX-License-Identifier: Apache-2.0 -->
# Spec delta: maintenance

## MODIFIED Requirements

### Requirement: Script Inventory

The following scripts SHALL be implemented as literate meta-script notes in Phase 1–2.
Each is offline and deterministic (INV-6).

The vault does **not** project effort state. No fleet script renders a board, dashboard, or
carry-over list of outstanding efforts: the vault exists to distil insight, and tracking
outstanding effort is a distinct lens delegated outside it. A projection with no consumer is not a
neutral cost — it decays into a stale artifact that answers wrongly rather than admitting it cannot.

The vault likewise generates **no dated note format**. Capture has a home in `20-Claims/`; the
framework engages downstream of capture, refining accumulated ore into banked value (ADR-0032). A
dated log that only a human could author, and that git already records, is a lossy duplicate of the
commit history rather than a second source.

| Script note | Deploy target | Runtime | Purpose |
| --- | --- | --- | --- |
| `render-reconcile-script.md` | `99-Operations/bin/vault-render.py` | manual | Deploy Layer-0 code blocks to their in-tree targets; detect drift |
| `knowledge-lint-script.md` | `99-Operations/bin/vault-lint.py` | manual / pre-commit | Validate Treasury frontmatter and name conformance |
| `treasury-orphan-script.md` | `99-Operations/bin/vault-orphans.py` | manual | Report Treasury notes not linked from any Catalog index (INV-12); detection only |
| `secret-scan-script.md` | `99-Operations/bin/vault_secrets.py` | manual / pre-commit | Credential-format scanner (INV-7, ADR-0036): tiered patterns over staged content, a path set, or the object DB; `--selftest` proves the patterns fire |
| `ore-detect-script.md` | `99-Operations/bin/vault-refine-detect.py` | manual | Queue ore whose grade cleared the Sort gate |
| `bank-execute-script.md` | `99-Operations/bin/vault-refine-execute.py` | manual | Apply approved proposals from `_refine-approved/`; writes Treasury; one atomic commit per banked proposal (`bank: <stem>`) |
| `spoil-dump-script.md` | `99-Operations/bin/vault-dump.sh` | manual | Move a spent husk to `71-Spoil/`; one commit |
| `site-slag-script.md` | `99-Operations/bin/vault-slag.sh` | manual | Move an uneconomic effort to `70-Tailings/`; one commit |
| `tailings-reprospect-script.md` | `99-Operations/bin/vault-reprospect.py` | manual | List slagged efforts for re-evaluation; detection only |
| `naming-rules-script.md` | `99-Operations/bin/vault_naming.py` | manual | Naming validator SSOT; also emits `naming-rules.json` |
| `vault-lib-script.md` | `99-Operations/bin/vault_lib.py` | manual | Shared fleet plumbing: root resolution, config vocabulary, frontmatter access, scoped one-commit helper, fleet exit-code contract (ADR-0023) |
| `commit-gate-script.md` | `99-Operations/hooks/pre-commit` | git hook | Commit-gate: block non-conforming file names (INV-11) |
| `outbound-publish-guard-script.md` | `.claude/hooks/outbound-publish-guard.py` | harness hook | Claude Code `PreToolUse` guard (INV-14, ADR-0018): hard-deny vault-outward commands; loud ASK before public publishes — now render/reconcile-governed (R8) |
| `gh-invocation-guard-script.md` | `.claude/hooks/gh-invocation-guard.py` | harness hook | Claude Code `PreToolUse` guard (ADR-0045): `gh` invocation-form **allowlist** — `gh api` with a REST path and `gh auth status` permitted, `gh api graphql` excepted back into deny, every other form refused by default rather than permitted by omission. Emits `deny` or nothing, never `allow` |
| `relay-conformance-guard-script.md` | `.claude/hooks/relay-conformance-guard.py` | harness hook | Claude Code `Stop` hook (item 40): byte-checks the `next.sh` line the agent relayed against the driver's `.git/pr-flow/relay-line.txt` sidecar; blocks a mismatch **at most once per emission** (a self-contained loop guard), fails open otherwise. Deterministic, offline (INV-6) |
| `push-guard-script.md` | `99-Operations/hooks/pre-push` | git hook | Push-gate (INV-14): deny outbound push by default; permit a remote in `PUSH_ALLOWLIST` (full vault); for a remote in `PUBLIC_REMOTE_ALLOWLIST`, permit **only** paths matched by `99-Operations/schemas/publish-manifest.json` (`public_allow`), else refuse |

No script declares a `cron` runtime or a `schedule:`. `render` deploys code and marks it executable;
it does **not** install schedules, and nothing reads a `schedule:` field. A cadence a script cannot
install is a decoration, not a configuration (ADR-0028).

The **note filenames** follow the `silo-section-descriptor` naming convention (silo first, `script`
trailing). **Deploy targets are unchanged.** The `commit-gate` and `push-guard` hooks are deterministic
(INV-6): they read git state, `config.env`, and (for `push-guard`) the language-neutral
`publish-manifest.json` schema only — no network, no LLM.

The **`publish-manifest.json`** schema (`99-Operations/schemas/`) is a language-neutral, default-deny
allowlist of publishable framework paths, consumed by `push-guard-script` and by any future
public-export/mirror tool.

Sibling scripts import the shared modules (`vault_naming`, `vault_lib`) from **their own
directory** via `sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))`; the underscore
module names mark importable libraries (the `vault_naming` precedent).

Resolution is from the executing file's location, never from `$HOME` or an environment variable.
Under ordinary invocation the interpreter already places the script's directory first, so a
home-relative insert is redundant and merely *appears* to be the mechanism. It stops being
redundant exactly where it also stops being correct: with the script-directory prepend disabled
(`python3 -P`) or when a fleet member is imported rather than executed, the home-relative path is
the only resolver — and it names a location the fleet no longer occupies.

#### Scenario: Retiring a script removes its deploy target in lockstep

- **WHEN** a script note is removed from the inventory
- **THEN** its deploy target is deleted from the host in the same apply — `reconcile` iterates
  **notes**, so a deployed artifact whose note no longer exists is invisible to drift detection and
  would persist as operational code outside the render inventory (the R8 gap)

#### Scenario: Push-guard denies an un-allowlisted push

- **WHEN** `git push` runs from a deployed vault and the target remote URL is not listed in `PUSH_ALLOWLIST` or `PUBLIC_REMOTE_ALLOWLIST`
- **THEN** the `pre-push` hook aborts the push (non-zero) with an INV-14 message

#### Scenario: Push-guard applies the path-level manifest to a public remote

- **WHEN** `git push` targets a remote in `PUBLIC_REMOTE_ALLOWLIST` and the diff includes a path not in
  `publish-manifest.json` `public_allow`
- **THEN** the `pre-push` hook aborts with an INV-14 path-boundary violation; a push whose paths are all allowlisted
  is permitted

## ADDED Requirements

### Requirement: A Relayed Handoff Is Byte-Checked Against The Emission

A `Stop` hook (`relay-conformance-guard`, rendered from its literate note) SHALL compare the operator
handoff the agent relayed in its final message against the command the driver emitted, and SHALL
block the turn from completing when they differ — so that a relay which drifts from the driver's
copy-whole block (a dropped tag, a swapped path form, a reformat — the F43 recidivism) is corrected
at the point it occurs rather than trusted to the agent's election.

The driver SHALL write the canonical relay line to a sidecar (`.git/pr-flow/relay-line.txt`) whenever
it writes a saved plan, byte-identical to the command inside the copy-whole block (see "The Operator
Handoff Is Emitted As A Copy-Whole Block"). The hook SHALL read the agent's final message
(`last_assistant_message`), extract a `bash …/next.sh` line appearing inside a `START COPY`/`END COPY`
block, and byte-compare it to the sidecar.

The hook SHALL be bounded against an infinite loop **independently of any platform safeguard**: it
SHALL block **at most once per emitted step**, recording that it has done so keyed on the sidecar's
content; a repeat mismatch on the same emission SHALL fall through to a passive warning, never a
second block. The hook SHALL **fail open** — a missing sidecar, an absent relay block, a malformed
input, or any error SHALL exit 0 with no block, so the hook can never trap the session. The hook is
stdlib-only and offline (INV-6).

#### Scenario: A drifted relay is blocked once

- **WHEN** the agent's final message relays a `bash …/next.sh` line, inside a `START COPY`/`END COPY`
  block, that is not byte-identical to the driver's sidecar
- **THEN** the hook blocks the turn (exit 2) and names the correct line to copy
- **THEN** a repeat mismatch on the SAME emission falls through to a warning without blocking again —
  bounded to one block, so no loop is possible

#### Scenario: A verbatim relay passes

- **WHEN** the relayed `bash …/next.sh` line is byte-identical to the sidecar
- **THEN** the hook does not block; the turn completes normally

#### Scenario: A message with no relay block is ignored

- **WHEN** the agent's final message contains no `bash …/next.sh` line inside a copy block
- **THEN** the hook does not block, regardless of the sidecar's state

#### Scenario: The hook fails open

- **WHEN** the sidecar is absent, the input is malformed, or any error occurs
- **THEN** the hook exits 0 with no block — it can never trap the session
