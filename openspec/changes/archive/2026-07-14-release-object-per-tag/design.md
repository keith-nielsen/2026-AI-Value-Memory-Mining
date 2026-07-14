<!-- SPDX-License-Identifier: Apache-2.0 -->
# Design — release-object-per-tag

## 1. The guard defect, precisely

`outbound-publish-guard.py` (ADR-0018) has two jobs: (1) HARD DENY vault-outward commands; (2) loud
ASK before a public publish. Both keys are wrong at the edges:

```
in_vault = bool(VAULT) and (cwd == VAULT or cwd.startswith(VAULT + "/") or VAULT in cmd)
if in_vault and OUTWARD.search(cmd):  emit("deny", …)   # job 1
if PUBLISH.search(cmd):               emit("ask",  …)   # job 2
```

- `cwd` is always the vault root in a live session; a command that `cd`s into the sibling framework
  repo still reports `cwd == VAULT` ⇒ **false DENY** on legitimate non-vault publishes.
- `OUTWARD` includes `git push`; `PUBLISH` does **not**. A framework-repo `git push` therefore
  matches neither DENY (once the false-positive is fixed) nor ASK ⇒ **silent defer** ⇒ unprompted push
  possible in a permissive mode.

## 2. The fix — effective-target scoping + universal outward ASK

**Effective target.** Determine the directory (or named repo) the command actually acts on, not the
shell's reported cwd:

- a leading `cd <path> &&` → `<path>` (this is exactly how cross-repo commands are issued);
- `git -C <path>` → `<path>`;
- `gh … -R <owner/repo>` → an explicitly named GitHub repo (not the local vault working tree);
- otherwise → the reported `cwd`.

`in_vault` becomes true only when the effective target resolves **inside** `$VAULT`, OR the command
references the vault path as an operand while performing an outward op (the conservative
`VAULT in cmd` clause is retained — erring toward DENY on any outward op that names the vault path is
safe and matches INV-14's intent). A `-R <owner/repo>` / `cd`/`-C` to a non-vault path is **not**
in-vault.

**Universal outward ASK.** Job 2 fires on `OUTWARD.search(cmd) or PUBLISH.search(cmd)` — i.e. any
outward-replication (`git push`, `git remote add`, `gh repo create`, `gh release …`) or distribution
publish (`npm/yarn/pnpm publish`, `twine`, `docker push`, `cargo`, `gem`) that was **not** hard-denied
in job 1 raises the ASK. No outward op can silently defer.

Resulting decision table:

| Command (effective target) | Before | After |
|---|---|---|
| vault-outward `git push` / release / remote-add | DENY | **DENY** (unchanged) |
| framework-repo `gh release create` | DENY (false) | **ASK** |
| framework-repo `git push` | DENY (false) → would be silent | **ASK** |
| read-only cmd merely *mentioning* a trigger token, non-vault target | DENY (false) | ASK (conservative) |
| `git commit -m "…push…"` (message contains a token) | (DENY if at vault cwd) | defer (no false positive) |
| `git -C <path> push` (was uncaught by `OUTWARD`) | silent defer | ASK / DENY per effective target |
| distribution publish (npm/twine/docker/…) anywhere | ASK | **ASK** (unchanged) |

**Banner.** The ASK banner is generalized so it reads correctly for both a plain push and a public
publish (it currently says only "PUBLISH TO A PUBLIC … LOCATION"). It states: this sends code/data to
a remote — permanent, review the summary + `proposal.md` before Yes — keeping the three deliberate-
confirmation checks.

**What the guard does *not* do:** it does not weaken the vault DENY, does not auto-allow anything, and
does not itself read `proposal.md`. It is the structural hard stop; being an ASK, the agent physically
cannot execute the command without an explicit human Yes, in any permission mode.

## 3. The informed pause (ceremony, not code)

The hard stop is only as good as the human's information at the moment of Yes. So the *ceremony*
(documented in `CONTRIBUTING.md` + `AGENTS.md`) requires: **before triggering any outward op** — the
merge, the tag push, the release — the agent presents (a) a one-screen overview summary of what is
about to go out, and (b) the **absolute path** to the governing `proposal.md` for full review, then
waits for explicit `Approved`. This is the standing Gate-4 ritual, now stated as a general rule for
outward ops, not just constitution overrides. The operator's scrutiny level is theirs to choose; the
system's duty is to make the material present and the stop unskippable.

## 4. Release-per-tag ceremony

Documented final steps of a ship, after PR merge to `main`:

```
1. git tag -a vX.Y.Z -m "vX.Y.Z — <title>"      # annotated
2. git push origin main --follow-tags            # ASK hard-stop (guard) → operator Approves
3. gh release create vX.Y.Z --verify-tag --latest \
     -t "vX.Y.Z — <title>" -n "<notes from tag/CHANGELOG>"   # ASK hard-stop → operator Approves
4. VERIFY: gh release view vX.Y.Z  →  must exist and be marked Latest   # parity check
5. Mirror the vault-template guard/hook updates into the live vault (operator action)
```

Parity is guaranteed **at ship time** by step 4 — the release is created and verified as part of the
same ceremony that cuts the tag, so a tag can never again exist without its Release. No separate
drift-scanning CI job is added (that would need a networked, authenticated GitHub call, against the
INV-6 offline-fleet posture); parity is a ceremony verification step, not a deterministic-fleet script.

## 5. Why one change, not two

The policy (agent/operator creates a Release per tag) is only *executable by the agent* because the
guard fix routes framework-repo release/push to the ASK hard-stop instead of a false DENY; and the
guard's ASK is what makes the release step the informed hard-stop the operator requires. Policy and
enabler are interdependent — one purpose: **every version tag ships with a gated, verified GitHub
Release.**
