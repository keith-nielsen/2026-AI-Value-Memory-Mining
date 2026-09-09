# Resolve render's operands from one root, and correct the gate that misdescribed it

## Why

`vault-render.py` reads its notes from the root `_vault_root()` resolves, but resolves each note's
**relative** `deploy_target` against the **process working directory** — two mechanisms, never
joined. When they name different trees the tool compares one vault's notes against another vault's
files and prints `ok`.

Found 2026-09-08 while validating a scratch harness *before* trusting it for a change to a restricted
area. The harness reported **`reconcile 15/15 ok, exit 0`** while comparing the live vault's notes
against a clone's deployed hooks — a clean pass, measuring the wrong tree, produced by the instrument
built to make the change safe. Reproduced four times; the live vault was never written to.

**`render` mode is the same defect with a write.** The same CWD-relative target is passed to
`write_text()`, so running it from another tree deploys this vault's code blocks into that tree.
Read from the source, deliberately not executed.

⚠ **A second finding, and the reason the first was possible.** The cold-start gates state the fleet is
*"env-free (root self-resolution, ADR-0023)"*. `vault_lib.find_vault_root()` is **env-FIRST**:
`VAULT_ROOT` wins outright, the cwd walk is only a fallback. That claim is acknowledged at the start
of every session and nothing verified it — it is why the harness pinned nothing and silently measured
the live vault.

## What Changes

1. **`vault-template/99-Operations/scripts/render-reconcile-script.md`** — join a relative
   `deploy_target` to the resolved root; honour an absolute one as written. Edited in the literate
   note (INV-3), never in the rendered file.
2. **`vault-template/96-Runbooks/session-bootstrap-loader.md`** — correct the clean-ops gate to state
   env-FIRST resolution, and instruct pinning `VAULT_ROOT` whenever the target is not the tree you
   stand in.
3. **`tests/test_render_root_resolution.py`** — three tests, one of them deliberately labelled as
   *not* discriminating.
4. **Spec delta** — two requirements: every operand resolves from one root, and a documented
   behaviour claim is verified by a test.

## Impact

- **Not constitutional.** Neither target carries a `protects:` frontmatter key. ⚠ Archiving will sync
  the delta into `openspec/specs/maintenance/spec.md`, which **is** `protects:`-tagged — a
  `constitutional-impact` declaration is owed in this change's own directory before the PR.
- **Both edited files are LOCKSTEP** (PR #115), so `template-parity` proves the deploy-down.
- **Behaviour change is a narrowing, never a widening.** The tool reads and writes strictly fewer
  paths than before: only those under the resolved root. No caller gains reach.
- **Deploy-down is operator-run** — `99-Operations/` and `.claude/` are agent-write-denied by design,
  which the render note itself documents.

## Constitutional impact

Archiving syncs this delta into `openspec/specs/maintenance/spec.md`, whose frontmatter carries
`protects: [INV-2, INV-3, INV-6]` — all **Tier 0 (Inviolable)** per `constitution.md` §2. The gate
requires the question answered **in the tree**, in writing.

Checked against each protected invariant rather than asserted:

- **INV-3** (*operational scripts are literate meta-script notes; they reach the host via `render`,
  and drift is detected via `reconcile`, never auto-fixed*) — **strengthened, not relaxed.** The fix
  is made in the NOTE, never the rendered file, exactly as INV-3 requires. `reconcile` remains
  detection-only. What changes is that it now detects drift in the tree it was pointed at, rather
  than sometimes reporting on another one.
- **INV-6** (*deterministic scripts: no network, no LLM*) — untouched. The change is a path join;
  no I/O of any kind is added.
- **INV-2** (*one commit per automated change*) — untouched; no commit ceremony is altered.

**The behaviour change is a narrowing.** After the fix the tool reads and writes strictly fewer paths
than before — only those under the resolved root. No caller gains reach, no guarantee is relaxed, and
no check is removed. The added spec requirements constrain future tools; they grant nothing.

```constitutional-impact
touches: openspec/specs/maintenance/spec.md
protects: [INV-2, INV-3, INV-6]
overrides: none
basis: ADDED requirements plus a path-join defect fix; INV-3 note-authored and detection-only both preserved, INV-6 unchanged; the tool's reach narrows to the resolved root and no authority is granted
```

## Verification

**The red proof, and what it exposed.** A first cut of the cross-tree test **passed against the
defect**: the broken code read the wrong tree, found a difference, and reported `DRIFT` for entirely
the wrong reason. The assertion could not separate a correct verdict from a coincidental one.

Rebuilt to discriminate — tree A internally consistent, tree B's target deliberately different:

| | fixed | broken |
|---|---|---|
| `VAULT_ROOT`=A, cwd=B | `ok`, exit 0 | `DRIFT`, exit 1 ← names a tree nobody asked about |

Measured against the pre-fix note: **2 of 3 tests fail.** The third is labelled non-discriminating in
its own docstring rather than counted as coverage — with cwd == vault, fixed and broken resolve
identically, so it passes either way.

Full suite: **389 passed** (386 baseline + 3).
