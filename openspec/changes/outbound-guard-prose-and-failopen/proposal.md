<!-- SPDX-License-Identifier: Apache-2.0 -->
# Change: outbound-guard-prose-and-failopen

## Why

Hardening-queue item 33's full-estate review found **four** defects in the INV-14 `PreToolUse`
outbound guard. A purely local `git commit` on the framework repo was HARD-DENIED twice (2026-08-27)
because the guard regexes the raw command string, so a commit message that *documents* a publish call
trips it; and target resolution needs a genuinely-leading `cd`, which the runbook-mandated
`source config.env; cd $FRAMEWORK_ROOT && …` idiom is not. The review also found a fail-open (the guard
takes its subject from the environment and returns "not the vault" when the env is unset) and an
inverted deny-hint (silent in the common case, loud in the rare one).

The framing that shaped the fix: **this guard is a belt, not the wall.** The load-bearing INV-14 push
barrier is the env-free, fail-closed `pre-push` hook plus the vault's remotelessness — so these changes
make the belt annoy real work less and stop it failing open, *without* touching the true-positive set.

## What Changes

Four fixes to `outbound-publish-guard-script.md`, composed so they don't tangle (D1 changes the
trigger, D2 the target resolver, D4 reuses that resolver for its env-unset fallback, D3 the message):

- **D1 — prose is data.** `_strip_arg_prose` blanks `-m`/`--message`/`-F`/`--file` argument VALUES
  before matching, so a message naming an outward command no longer trips `OUTWARD`/`PUBLISH`. Heredoc
  bodies are **not** stripped (a heredoc can be executed — blanking it could hide a real command).
  Applied only to the match/resolution inputs; the driver-emission exact-match and every displayed
  `command:` keep the original text.
- **D2 — the mandated idiom resolves.** `_LEAD_CD` tolerates an optional leading `source <file>;` /
  `. <file>;` before the `cd`, so a sibling-targeted bootstrap command is no longer mis-attributed to
  the cwd (the vault). Narrow prefix; the trusted `cd` is still the first one.
- **D3 — the deny explains itself.** `_unresolved_redirect_hint` now also names the common
  "no redirect recognised → target fell back to the cwd" case, previously a silent refusal.
- **D4 (light-touch) — never fail open.** When neither `$VAULT_ROOT` nor `$CLAUDE_PROJECT_DIR` is set,
  `_targets_vault` identifies the vault by its marker (`99-Operations/config.env`) at the effective
  target via `_has_vault_marker`, rather than returning `False`. **Only the fail-open line changes**;
  the env-set path (every normal session) is byte-for-byte unchanged, so it can only ADD protection
  where the guard previously did nothing.

## Impact

- Fewer false denials of legitimate local work (commit messages, the mandated `cd` idiom); a
  self-explaining deny; and no fail-open when the environment is dropped.
- **The true-positive set is unchanged** — proven by tests that pair each false-positive removal with a
  true-positive that is still denied, and by the retained mutation test.
- INV-14 is *strengthened* on net (D4 closes an under-fire) while its false-positive surface shrinks.
- **Deploy-down owed:** re-render the guard note into the live vault (operator-run). Bundle it with
  item 35's reconcile re-render — one `template-mirror` + `render`.

## Constitutional impact

The delta ADDS a requirement to `openspec/specs/access-control/spec.md` (INV-14, Tier-0). It narrows
false denials and closes a fail-open; it does not relax the vault-outward or irreversible-outward
denials. `overrides: none`.

```constitutional-impact
touches: openspec/specs/access-control/spec.md
protects: [INV-14]
overrides: none
basis: refine a Tier-0 control — narrower false-denies + a closed fail-open, true-positive set intact
```

## Verification

- Red-first, each defect, with a paired true-positive:
  - D1: a commit message naming a publish → defer; a real release-create with a `--notes` message and a
    real push next to a stripped `-m` → still deny.
  - D2: `source 99-Operations/config.env; cd <sibling> && git push` → not vault-denied; the same idiom
    into the vault → still denied.
  - D3: a no-redirect vault-outward deny names the cwd fallback.
  - D4: env unset + a marked vault → deny; env unset + no marker → ask (inert, not silently allowed);
    env set → behaviour unchanged.
- The existing REST-coverage and mutation tests stay green (the mutation anchor is updated to the
  renamed call arg).
- The repo hook is re-rendered byte-identical to the note (F29).
- Suite **536 passed**; `openspec validate --all --strict`, markdownlint, and the INV-6 offline checks
  all clean.
