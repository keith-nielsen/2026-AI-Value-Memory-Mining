# Prove a markdown reformat preserved content, with an instrument rather than review

## Why

A corpus-wide formatting sweep is unreviewable by eye. The diff is hundreds of lines of moved
whitespace and a single altered word hides in it perfectly.

That is not hypothetical. On 2026-08-27 a `markdownlint --fix` pass stripped the trailing space from
`` `trail ` `` in `openspec/specs/naming-rules/spec.md` — a code span whose trailing space **was the
test input**. The scenario was left asserting that `trail`, a **valid** name, must be rejected, while
still annotated "(trailing space)". MD038 reported exactly one finding on `main` and this was it. The
autofix cannot distinguish a significant space from a sloppy one, and:

- no reviewer caught it, across a 623-line diff;
- no test caught it — nothing in this repo compares content across a reformat;
- the sweep's own commit message asserted *"content provably unchanged"*, and that claim was wrong
  for the one file where it mattered, in a spec carrying `protects: [INV-11]`.

The gap is specific: this estate verifies **artifacts** and does not verify **its formatters**. A
reformat is the one class of change where the diff's size is itself the concealment.

⚠ **Second, symmetrical failure.** The same absence produced a *false* finding. Four `###` headings
vanish from `CHANGELOG.md`, which reads as re-classified release history and was reported as damage.
Measuring each affected entry's `(release, section)` before and after showed **4/4 unchanged** — a
lossless consolidation of duplicate sections within one release. Without an instrument, a reviewer
guesses in both directions.

## What Changes

1. **`tools/md_content_check.py`** — a deterministic, offline, detection-only checker. It compares the
   token multiset of two revisions of every changed markdown file with all whitespace collapsed, and
   classifies each file `identical` / `reordered` / `changed`. Structural tokens — fences, table
   separator rows, bare pipes, list bullets — are excluded, so formatting is invisible and content is
   not. Accepted differences are declared per path with `--allow`, which records acceptance instead
   of weakening the check.
2. **`tools/md_content_check.py --selftest`** — proves both directions before the tool is trusted,
   matching the idiom `secret-scan` already uses (*"a scan that cannot fail proves nothing"*).
3. **`tests/test_md_content_check.py`** — 21 tests. Every formatting-insensitivity test is paired
   with a mutation that MUST be caught, including the real 2026-08-27 defect reproduced verbatim.
4. **Spec delta** — one ADDED requirement in `maintenance`.

## Impact

- **Additive and detection-only.** No existing tool, gate, workflow or CI job is modified. The
  checker writes nothing and is not wired into CI by this change.
- **No new dependency.** Stdlib only — the INV-6 posture, and no enlargement of the trust ring.
- ⚠ **Not wired into CI, deliberately.** This change adds the instrument and its proof. Making it a
  required gate changes merge behaviour for every markdown PR and is a separate decision with its own
  blast radius. Stating this plainly because an instrument nobody runs is the failure mode this
  estate already has six recorded instances of — the honest position is that this change makes the
  check *possible and proven*, not *automatic*.
- **The tool's blind spot is stated, not discovered later.** Tokens made only of pipes, colons,
  hyphens and spaces are structural, so a prose edit whose ONLY difference is a standalone dash is
  not detected. Documented in the module and pinned by
  `test_documents_the_standalone_dash_blind_spot`, so it cannot widen silently.

## Constitutional impact

Archiving syncs this delta into `openspec/specs/maintenance/spec.md`, whose frontmatter carries
`protects: [INV-2, INV-3, INV-6]` — all **Tier 0 (Inviolable)** per `constitution.md` §2. Checked
against each rather than asserted:

- **INV-2** (*one automated change, exactly one commit*) — untouched; no commit ceremony is altered.
- **INV-3** (*operational scripts are literate meta-script notes, rendered to the host, drift detected
  never auto-fixed*) — **not engaged**: `tools/` holds repo-owned maintainer tools, not
  `99-Operations/scripts/` meta-script notes, and nothing here is deployed into a vault by `render`.
  The detection-only posture INV-3 requires of `reconcile` is mirrored here by choice: this checker
  reports and never edits.
- **INV-6** (*deterministic scripts: no network, no LLM*) — **upheld and verifiable**: stdlib only,
  no imports beyond `argparse`/`collections`/`re`/`subprocess`/`sys`, and the only subprocess calls
  are local `git` reads.

The change is **purely additive**: it adds a requirement and a tool, removes nothing, relaxes no
guarantee, and grants no authority to any caller.

```constitutional-impact
touches: openspec/specs/maintenance/spec.md
protects: [INV-2, INV-3, INV-6]
overrides: none
basis: ADDED requirement plus a new stdlib-only detection-only tool; INV-3 not engaged (repo tool, not a rendered meta-script note) and its detection-only posture mirrored anyway, INV-6 upheld with no network, INV-2 untouched; nothing is removed or relaxed
```

## Verification

**The suite was shown to fail before it was trusted.** A mutation matrix applied five mutants to the
checker itself, each **in isolation** — compounding mutants is what made an earlier matrix in this
estate meaningless, because attribution requires isolation:

| mutant | result |
| --- | --- |
| M1 `is_structural` always True | **KILLED** — 14 failed |
| M2 `compare` always reports identical | **KILLED** — 12 failed |
| M3 whitespace not collapsed | **KILLED** — 9 failed |
| M4 bullets no longer structural | **KILLED** — 2 failed |
| M5 `reordered` collapsed into `identical` | **KILLED** — 1 failed |

**5/5 killed**, the tool restored byte-identical afterwards, and the suite passes again post-restore.

**One test failure during development was a real finding, not noise.** `is_structural("-")` returned
True by accident — a bare list bullet fell through the table-separator regex. Rather than widen the
test to accept it, the classification was made explicit with its own pattern and the resulting blind
spot documented and pinned.

**End-to-end against real data** — run over the actual formatting sweep
(`main..docs/md-lint-phase-a-fix-sweep`, 46 files):

| verdict | count |
| --- | --- |
| identical | 40 |
| changed | 4 |
| added-or-removed | 2 |

It names exactly the four files a hand analysis found, and exits `1`. The four are the emphasis-style
swap, the CHANGELOG consolidation, a blockquote marker, and the disable comment on the repaired line.

Gates on this branch:

| gate | result |
| --- | --- |
| `pytest tests/ -q` | **407 passed** (386 baseline + 21) |
| `openspec validate --all --strict` | **7 passed, 0 failed** |
| `markdownlint` on the new files | **0 findings, exit 0** |
| `markdownlint`, whole tree | 1138 — `main`'s existing baseline, **delta 0** from this change |

The whole-tree count is `main`'s untouched corpus: this branch is cut from `main` and deliberately
does not carry the formatting sweep, which is a separate change. What matters here is that this
change adds **zero** findings of its own.
