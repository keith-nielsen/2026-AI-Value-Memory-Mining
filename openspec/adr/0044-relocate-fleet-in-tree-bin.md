<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0044 — The rendered fleet lives inside the tree it serves

**Status:** **Proposed** (Gate-4 pending — human-only sign-off, constitution §5)
**Date:** 2026-08-18
**Change:** `relocate-fleet-in-tree-bin`
**Relates:** **ADR-0023** (env-free fleet, root self-resolution — the principle this extends from
*root* to *module* resolution); **ADR-0022** (OS-enforced write scope — unchanged by this);
**ADR-0027** (effective-target resolution); **ADR-0040** (archive on the feature branch);
failure **F15** (*a deployed vault is standalone*).

## Context

The rendered Layer-0 fleet deployed to `~/bin/` — a user-global directory outside every repository.
Eleven of fourteen deploy targets lived there; the two git hooks and the harness guard were already
in-tree.

Four grounds of principle, and one measured defect:

1. **It contradicts a principle this operation had already codified.** F15's corrective is *"a
   deployed vault is standalone."* A vault whose operational fleet installs into the user's home is
   a tree plus a side-load. There is a CI job named for the principle — `Standalone-vault lint
   (F15)` — but it only checked that `vault-template/` referenced no framework-repo path. **`~/bin`
   walked straight past the lint written to enforce standalone-ness**, for months.
2. **Multi-vault version skew was unrepresentable.** Two vaults, or a vault and a fork at a
   different version, share one `~/bin`. The last render silently wins, with no way to tell.
3. **Fork ergonomics.** A fork should inherit a tree that already contains its tools, not
   instructions to contaminate a namespace that belongs to the user.
4. **It manufactured an authority problem.** `render` was operator-only *because* its targets sat
   outside the agent's write scope. Moving the targets in-tree dissolves that reason repo-side,
   while leaving the vault-side protection exactly where it was.
5. **`~/bin` was not reliably on `PATH` — measured, not inferred.** The two mechanisms that build it
   are disjoint and never both run: a login shell reads `~/.profile` (which adds `~/bin`) but skips
   the interactive `~/.bashrc`; a non-login shell does the reverse. Measured from a clean
   environment:

   ```
   bash -lc  (login, non-interactive) → /home/administrator/bin/vault-lint.py
   bash -ic  (interactive, non-login) → NOT-FOUND
   bash -c   (neither)                → NOT-FOUND
   ```

   The fleet was invisible to cron, systemd user units, `ssh host 'cmd'`, and any plain `bash -c`.
   The corpus had flip-flopped on this question — *"`~/bin` is not on PATH"* corrected to *"IS on
   PATH"* — because **both readings are half-right and neither states the condition.**

## Decision

Relocate the eleven host targets to **`99-Operations/bin/`**, inside the vault tree. The three
in-tree targets do not move.

**Deliberately inside protected Layer 0.** INV-4/5 continue to deny the agent. That is wanted: the
agent must not be able to rewrite its own guards. This buys containment, forkability and
repository-side runnability — **not** loosened protection. Vault-side `render` stays operator-only.

**No `$VAULT_BINS` variable.** ADR-0023 exists *because* an env dependency broke the fleet: probe P5
crashed with `KeyError: 'VAULT_ROOT'` in a fresh tool shell, and the exact-match exclusion forbade an
env prefix, making SE-5 unprovable. A new variable reintroduces precisely that, in the more fragile
direction: it is *derivable* from `$VAULT_ROOT`, so it would be a **second SSOT for one location** —
unset or skewed, it yields a silent wrong-tree resolution, which is the multi-vault skew this change
exists to end.

**Sibling modules resolve from the executing file's own location**, extending ADR-0023's principle
from root resolution to module resolution. The same applies to the git hooks, which invoked the
fleet by `${HOME}/bin` path and now derive it from their own.

**Render output is git-ignored and is not a lockstep prefix.** Its single source is the notes.
Tracking it would give one piece of code two homes and make every render a diff to review;
comparing it against a template that ships generators rather than output would report permanent
drift. Parity compares hand-maintained scaffold; render/reconcile compares generated output against
the note that produced it.

**The path contribution is appended and idempotent**, from the vault configuration only — never a
shell profile. Appended because nothing collides: every member carries the `vault-`/`vault_` prefix,
which this change finally writes down as a rule rather than leaving as an accident.

## Options considered

- **(a) Relocate to `99-Operations/bin/` (chosen).** Containment without any change to permission.
- **(b) Keep `~/bin`, add an in-tree render-scope flag.** Rejected: routes around the gap instead of
  removing it, and leaves grounds 1–3 and 5 untouched.
- **(c) Relocate to a `$VAULT_BINS`-configured location.** Rejected on ADR-0023 grounds above — a
  second SSOT for a derivable fact.
- **(d) Relocate to `~/.local/bin`.** The systemd `file-hierarchy(7)` standard location, and
  genuinely better than `~/bin` — but it is still user-global, so it fixes only ground 5 and leaves
  1–3 exactly as they were.
- **(e) Do nothing.** Rejected: ground 5 is a live defect, not a design preference.

## Consequence

- A fork gets a self-contained tree; `git clone` plus `render` yields a working vault with no
  user-global side-load and no edit outside the repository.
- Multi-vault skew becomes representable — each vault carries its fleet at its own version.
- The fleet becomes reachable from **non-login shells**, closing ground 5.
- CI gains realism: the harness renders where the fleet actually ships, rather than into a throwaway
  `$HOME/bin` that no deployment resembles.
- The `Standalone-vault lint (F15)` can finally see this class of violation — extended here to
  refuse any `deploy_target` outside the tree, and demonstrated red on the pre-move tree (11 of 14).
- `~/bin` is decommissioned.

## Sacrifice

Stated plainly, because an options list that reads as costless is not a decision record.

- **A fresh clone no longer has a runnable fleet until `render` is run.** Under `~/bin`, a second
  vault on a machine that already had the fleet installed inherited working tools immediately. That
  convenience is given up deliberately: it was the same property as ground 2, seen from the other
  side. Convenience and skew were one mechanism, and both are removed together.
- **A bare `vault-lint.py` stops working in shells that have not sourced the vault configuration.**
  Under `~/.profile` the fleet was on `PATH` in every login shell, including in other directories.
  Now the contribution is opt-in and scoped. This is a real reduction in ergonomics for the
  operator's habitual shell, accepted in exchange for the contribution ending when the shell exits.
- **The generated fleet now sits inside a protected silo**, so `render` remains operator-only and the
  agent cannot self-repair a broken deployment. The alternative — placing generated code where the
  agent can write it — would let an agent rewrite the guards that constrain it, and is refused.
- **`__pycache__` would otherwise be written into governed space.** Handled here with
  `sys.dont_write_bytecode`, but it is a new class of hazard the old location did not have: the
  tree now receives generated bytes that no drift check inspects. `~/bin/__pycache__` already held
  the compiled corpse of a script deleted a month earlier, invisible to `reconcile` because
  `reconcile` iterates notes — the same blind spot, now pointed at a protected silo.
- **One more thing must be deployed down by hand.** The vault's `.gitignore` is a SEED file, not a
  lockstep prefix, so the ignore rule reaches a live vault only through a targeted operator edit. A
  vault that misses it will track its own render output.
