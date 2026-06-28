---
type: knowledge
title: git-bisect-regression-hunting
pillars: [technology]
grade: gold
stage: refined
crucible: false
created: 2026-05-30
updated: 2026-05-30
tags: [git, debugging]
---
# git bisect: regression hunting is a binary search

Finding the commit that introduced a regression is not a linear hunt — it is a
**binary search** over history. `git bisect` automates that search; `git bisect run`
removes the human from the loop entirely.

**The reframe (the durable value):** any regression with a known-good and known-bad
point can be located in ~log2(N) tests instead of up to N. 60 commits → ~6 tests,
not 60.

**Manual loop:**
```
git bisect start
git bisect bad HEAD
git bisect good <known-good-ref>
# build + test each checkout, then: git bisect good | git bisect bad
git bisect reset   # restore original HEAD when done
```

**Automated loop (the real unlock):**
```
git bisect start HEAD <known-good-ref>
git bisect run ./check.sh   # exit 0 = good, non-zero = bad, 125 = skip/untestable
```

**Preconditions that must hold:**
- The test must be **deterministic** — a flaky test converges bisect on the wrong commit.
- The property must be **monotonic** — good stays good until the single bad commit.
  A bug that appears and disappears breaks the binary-search assumption.
- Use exit code **125** to skip commits that can't be evaluated (e.g. unrelated build break).

**Generalization:** `git bisect terms` lets you bisect on *any* binary property, not
just "broken" — e.g. a perf regression, by scripting a benchmark threshold.

## Provenance / Changelog

Distilled from a 2026-05-29 effort (status: ore, grade gold). Verified the manual and
automated loops against a real nightly-build regression (good `v2.3.0` → bad `HEAD`,
culprit found in 6 steps over ~60 commits, ~20 min vs. ~3 h by hand). The flaky-test
and monotonicity caveats are first-hand: 15 min was lost to a false convergence caused
by an intermittent test before the cause was identified. The command reference itself
was deliberately not transcribed (it lives in `man git-bisect`); only the reframe and
the non-obvious preconditions were kept.

<!--
  This is BULLION — refined, verified knowledge in 40-Treasury/. Compare it to the
  Dig notes in 02-site-walkthrough/02-site-walkthrough.md: the bullion is shorter, denser, and
  free of the exploratory mess. It distills; it does not transcribe. In a real vault
  this file lives at 40-Treasury/git-bisect-regression-hunting.md (note the kebab-case
  stem — INV-11) and is linked from 40-Treasury/Catalog/technology-domain-index.md.
-->
