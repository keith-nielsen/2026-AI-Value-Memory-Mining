<!-- SPDX-License-Identifier: Apache-2.0 -->
# Change: relay-conformance-guard

## Why

Item 39 made the driver emit the operator handoff as a copy-whole block, so relaying it verbatim is
the *lazy* path. That reduces the F43 relay-recidivism but does not *catch* it: the agent can still
retype the line and drop the tag or swap the path form. Per ADR-0034 and F42/F43, a rule applied by
the agent's election has the reliability of memory; the reproducible-by-construction fix is a runtime
control that compares what the agent relayed against what the driver emitted.

Only a `Stop` hook sees the artifact where the drift occurs — the agent's own message — so this is the
one mechanism that can enforce it at the point of failure. Item 40 is that hook.

## What Changes

- **The driver writes a canonical relay-line sidecar.** When `pr-flow.py`'s `emit()` writes a saved
  plan, it also writes the exact relay line (`bash <saved-plan-path>   # <tag>`) to
  `.git/pr-flow/relay-line.txt` — the same string item 39 puts in the copy-whole block.
- **A new `Stop` hook** (`relay-conformance-guard-script.md` → `.claude/hooks/relay-conformance-guard.py`)
  reads `last_assistant_message`, extracts a `bash …/next.sh` line that appears **inside a
  `START COPY`/`END COPY` block**, and byte-compares it to the sidecar. On a mismatch it **blocks**
  (exit 2) with the correct line, so the agent re-relays it verbatim.
- **Registered as a `Stop` hook** in `.claude/settings.json` in both roots (SEED, per-instance; hook
  registration is not verified by parity — item 32).

## The loop hazard, and how it is bounded

A `Stop` hook that blocks makes the agent continue; if it blocked on every fire it could loop. This
version's Stop-hook contract documents **no `stop_hook_active` field and no platform loop-guard**, so
the hook provides its own: it **blocks at most once per emitted step**, keyed on a hash of the
sidecar written to `.git/pr-flow/relay-block-marker`. Once it has blocked for a given emission, a
repeat mismatch on the *same* emission falls through to a passive stderr warning (exit 0) — never a
second block. A new emitted step changes the sidecar hash and re-arms exactly one block. So the
worst case is a single wasted block-and-retry, never a loop, independent of any platform safeguard.
Every parse failure, missing sidecar, or unreadable input **fails open** (exit 0) — the hook can
never trap the session.

## Impact

- A new control surface (a `Stop` hook) — hence Gate 4.
- No change to any existing hook or the driver's decisions; the driver gains one sidecar write.
- Completes the recidivism cluster: item 39 makes the correct relay lazy, item 40 makes a wrong one
  caught.

## Constitutional impact

The delta ADDS a requirement to `openspec/specs/maintenance/spec.md`
(`protects: [INV-2, INV-3, INV-6]`).

- **INV-6** — the hook is stdlib-only, offline, deterministic (reads files, no network/subprocess);
  it fails open on any error. Untouched in substance.
- **INV-2 / INV-3** — untouched; no commit-structure or literate-note/render-relationship change
  (the hook is itself a literate note rendered like the others).

Additive; engages none of the three, `overrides: none`. Surfaced for sign-off because it touches a
`protects:`-tagged spec and is a new control surface.

```constitutional-impact
touches: openspec/specs/maintenance/spec.md
protects: [INV-2, INV-3, INV-6]
overrides: none
basis: ADD-only
```

## Verification

- Red-first: a mismatched relayed line is not blocked before the hook exists.
- The hook blocks (exit 2) on a mismatch, allows (exit 0) a byte-exact relay, and ignores a message
  with no relay block.
- **The block-once-guard is proven:** a second identical mismatch for the same emission falls through
  to exit 0 (no loop); a new emission re-arms one block.
- Fail-open: missing sidecar, malformed JSON, and unreadable input each exit 0 with no block.
- The driver writes `relay-line.txt` byte-identical to the copy-whole block's command.
- **Historical regression** (operator-requested): the hook was run against the reconstructed
  relay-drift instances from the record — the 2026-08-25 tag strip (F43), this session's dropped tag
  and env-var/abspath swap, and an indented paste. It **found a real gap**: the first cut required
  `bash` at column 0 and silently passed an INDENTED relay (itself an F43 drift mode). Fixed to
  capture the leading whitespace and treat indentation as drift; all four modes now block, a correct
  relay does not, and the case is pinned by `test_an_indented_relay_is_caught`.
- Full suite, `openspec validate --all --strict`, and markdownlint all clean.
