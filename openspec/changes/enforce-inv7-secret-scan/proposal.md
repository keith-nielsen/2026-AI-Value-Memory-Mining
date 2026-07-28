<!-- SPDX-License-Identifier: Apache-2.0 -->

# Constitution Override: enforce-inv7-secret-scan

**Change type:** `constitution-override`, **conforming**
**Principle(s) affected:** `access-control` spec (`protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]`) — **ADDs** a Requirement. **No Tier-0/Tier-1 element is overridden or weakened**; INV-7 is *strengthened* from a stated prohibition to a mechanical one.
**Tier:** 0 (INV-7)
**Proposer:** Keith Nielsen
**Date:** 2026-07-28

---

## Why

INV-7 — *"No secrets in any vault file"* — is a Tier-0 **Safety** invariant and was enforced by
**nothing**. Not a hook, not a linter, not a CI job. A credential pasted into any note committed
cleanly, in both the framework repo and every deployed vault.

This was found by the 2026-07-28 Tier-0 enforcement audit, which read every hook,
`.claude/settings.json`, and all eleven CI jobs and asked one question per invariant: *what fires
without agent cooperation?* Of the nine live Tier-0 invariants, **three** had an answer (INV-4,
INV-5 kernel-enforced; INV-11 by the commit gate). INV-7 and INV-6 had none at all.

**The spec already states the rule and verifies the wrong thing.** The existing
`Requirement: Secrets Prohibition (INV-7)` says *"No credentials, API keys, tokens, or passwords
SHALL appear in any vault file"* — and its **sole scenario inspects the contents of two config
files.** That is a Factor-A check (configuration is as expected) standing in for a Factor-B
property (a secret cannot be committed). It is the same substitution catalogued as root cause
RC-C in the `github-canary-barium-lunch-investigation`, and the same shape ADR-0030 found in
INV-11: a rule that lives as text, enforced by nothing.

The sacrifice is small and real: a format-shaped false positive can block a legitimate commit,
and the gate adds one subprocess per commit.

## What Changes

The prohibition is unchanged. What changes is that it acquires a **mechanism**: a new Layer-0
meta-script (`secret-scan-script.md` → `~/bin/vault_secrets.py`) called by the existing commit
gate, plus a CI job scanning the framework repo's full object database.

Two design choices carry most of the weight and are stated in the spec, not left to the code:

- **Only the HIGH tier gates.** HIGH patterns are anchored vendor token formats (`ghp_` + 36
  chars, `AKIA` + 16, …) with a false-positive rate near zero. ADVISORY patterns
  (`password = "…"`) are reported by the standalone tool and **never consulted by the hook.**
  This is RC-E applied deliberately: *over-denial is camouflage.* This corpus discusses
  credentials constantly — its own audit notes would be a blocking scanner's most frequent
  victim, and a gate that fires on prose teaches its operator to bypass it.
- **Findings are redacted.** Matches truncate to four characters plus a length. A scanner that
  echoes what it found writes the secret into a terminal, a shell history and possibly a commit
  message — violating INV-7 while enforcing it.

---

## Gate 1 — CHECK (Impact Analysis)

**Principle being strengthened (restated):**

> INV-7 says the vault must never contain a credential. It is a Safety-band invariant because a
> leaked secret is not recoverable by editing the file — the credential is compromised the moment
> it exists, and every copy of the history keeps it. Nothing in the operation checked this. The
> invariant described an outcome and named no actor responsible for producing it.

**Blast radius — every artifact referencing this principle.**

**Enumeration transcript (mandatory — the checklist below is derived from it, and Gate 4 re-runs it):**

```transcript
$ grep -rn 'INV-7' --include='*.md' --include='*.json' --include='*.yml' . | grep -v node_modules | grep -v '^./openspec/changes/archive'
SECURITY.md:37:| INV-7 | No secrets in vault — credentials must never appear in vault files |
openspec/adr/0008-invariant-criticality-ordering.md:12:(INV-7: no secrets) — the opposite of their actual blast-radius relationship.
openspec/adr/0008-invariant-criticality-ordering.md:40:| INV-9  | INV-7 | No secrets in vault |
openspec/adr/0008-invariant-criticality-ordering.md:42:| INV-7  | INV-9 | Refined value is never discarded |
docs/USING-THIS-TEMPLATE.md:281:- No secrets in vault files (INV-7)
AGENTS.md:110:**Safety** — INV-4 (Bounded write) · INV-5 (Actor≠owner) · INV-6 (Offline scripts) · INV-7 (No secrets) · INV-8 (Crucible independence)
vault-template/CLAUDE.md:30:- No secrets in any vault file. (INV-7)
vault-template/00-Docs/README.md:157:| INV-7 | No secrets in any vault file |
openspec/project.md:52:- **INV-7 — No secrets in vault.** No credentials, keys, tokens, or passwords in
openspec/adr/0025-permit-agent-claims-capture.md:7:  `protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]`)
openspec/adr/0032-retire-daily-close-cycle.md:8:[`protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]`]
openspec/adr/0033-open-logbook-write-scope.md:7:`access-control` spec [`protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]`]
docs/research.md:116:- No secrets in vault files (INV-7)
openspec/specs/access-control/spec.md:3:protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]
openspec/specs/access-control/spec.md:125:### Requirement: Secrets Prohibition (INV-7)
openspec/changes/add-telemetry-segment/design.md:4:The vault's safety invariants (INV-4, INV-5, INV-7) define what automated processes
(new files from this change omitted: secret-scan-script.md, commit-gate-script.md, ci.yml)
```

```transcript
$ grep -rnoE '\b1[0-9]\b[^.]{0,45}(script|meta-script|hook)' README.md AGENTS.md docs/*.md openspec/specs/*/spec.md vault-template/00-Docs/*.md
README.md:113:13 literate meta-script
docs/research.md:134:11 + naming validator + pre-commit hook
docs/USING-THIS-TEMPLATE.md:18:12+ | For all operational script
docs/USING-THIS-TEMPLATE.md:23:13); Linux/POSIX only — bash hook
docs/USING-THIS-TEMPLATE.md:282:11) — changes cascade to the hook
docs/obsidian.md:8:13 script
docs/obsidian.md:147:13 script
```

**Per-hit disposition of the count sweep** (4 of 7 are regex false positives, stated rather than silently dropped):

| Hit | Disposition |
|---|---|
| `README.md:113` "Layer 0: 13 literate meta-scripts" | **CHANGE → 14** |
| `docs/obsidian.md:8` "all 13 scripts" | **CHANGE → 14** |
| `docs/obsidian.md:147` "listing the 13 scripts" | **CHANGE → 14** |
| `docs/research.md:134` | false positive — matched `INV-11`, not a count |
| `docs/USING-THIS-TEMPLATE.md:18` | false positive — "Python 3.12+" |
| `docs/USING-THIS-TEMPLATE.md:23` | false positive — CI matrix "3.12 + 3.13" |
| `docs/USING-THIS-TEMPLATE.md:282` | false positive — `INV-11` |

```transcript
$ python3 -c "import json,pathlib; print(json.loads(pathlib.Path('tools/template-sync-manifest.json').read_text())['lockstep'])"
['99-Operations/scripts/', '99-Operations/schemas/']
```

→ **No manifest edit required.** Matching is directory-prefix, so the new script is in lockstep
automatically and `template-parity.py` will compare it without registration. Checked, not assumed.

**Checklist (derived from the transcripts above):**

- [ ] `openspec/specs/access-control/spec.md` — **ADDED** Requirement: *Secrets Prohibition Is Enforced at the Boundary*. The existing `Secrets Prohibition (INV-7)` Requirement is **left intact** (ADR-0030 pattern: add the enforcement Requirement beside the prohibition, do not rewrite the prohibition)
- [ ] `openspec/constitution.md` — **no change**; INV-7's text and tier are untouched
- [ ] `vault-template/99-Operations/scripts/secret-scan-script.md` — **new** meta-script (fence check: exactly 1 `python` fence, verified)
- [ ] `vault-template/99-Operations/scripts/commit-gate-script.md` — calls the scanner; rationale documents the three asymmetries with the INV-11 half
- [ ] `.github/workflows/ci.yml` — new `secret-scan` job (`fetch-depth: 0`, selftest then full object-DB scan)
- [ ] `tests/test_secret_scan.py` — 13 cases, negative controls included
- [ ] `README.md:113` · `docs/obsidian.md:8,147` — fleet count 13 → 14
- [ ] `README.md` ADR count 35 → 36 + reference `0036` — **CI-guarded** by `adr-count-lint`
- [ ] `CHANGELOG.md` — v0.1.35 entry
- [ ] `SECURITY.md:37` — INV-7 row may now name its mechanism (advisory, not required)
- [ ] `tools/template-sync-manifest.json` — **no change required** (directory-prefix lockstep, transcript above)
- [ ] `docs/glossary.md` / `vocabulary-lint` — **no new vocabulary**; "scanner", "credential", "redact" are not off-metaphor terms
- [ ] `vault-template/97-Molds/` — **no change**; this introduces no note type
- [ ] ADR reference — **new ADR-0036 required** (see Gate 4)

**Explicitly NOT changed:** the INV-7 prohibition text; the INV-11 half of the commit gate
(`--diff-filter=AR`, grandfathering intact); the fleet contract exit codes; `vault_lib`.

**Deliberately excluded from this change** (raised by the same audit, queued separately so the
blast radius stays honest):

- **INV-6** has zero mechanism and is the last Tier-0 invariant in that state.
- **`access-control` lines 68/73** still claim the commit gate enforces INV-4/INV-5. It does not —
  that moved to the kernel under ADR-0022, and line 293 says so explicitly. A stale false
  enforcement claim in the same spec this change edits. **Operator decision pending:** fold into
  this change (one ceremony, wider diff, must be declared in the PR scope block) or run separately.

---

## Gate 2 — PLAN (Migration + Regression)

**Migration plan:**

1. Author the ADDED Requirement in the change's `specs/access-control/spec.md` delta.
2. Land the mechanism (already implemented on `feat/enforce-inv7-secret-scan`, commit `2c0604b`).
3. Update the three real fleet counts; leave the four false positives alone.
4. Write ADR-0036; bump the README ADR count to 36 and reference `0036`.
5. CHANGELOG v0.1.35.
6. Ship via `tools/ship-release.py v0.1.35`; archive **on the feature branch before merge**.
7. Post-merge: `tools/template-mirror.py` → **operator** runs `render` (operator-only path) →
   `reconcile` zero drift. Until step 7 the live vault's gate is unchanged and INV-7 stays
   unenforced there; the repo half is live at merge.

**Regression tests that MUST pass before Gate 3:**

- [ ] `openspec validate --all` passes
- [ ] `constitution-lint` passes
- [ ] `vocabulary-lint` passes (no glossary change)
- [ ] `adr-count-lint` passes with 36
- [ ] `pytest tests/` fully green, including the 13 new cases
- [ ] `secret-scan` CI job green (selftest + full object-DB scan)
- [ ] `validate-scripts.sh` green — render, fence lint, reconcile zero drift with 14 scripts

---

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑
**All regression tests green:** ☑ (locally; two environment caveats stated below, neither masking a failure)
**CI green on this PR:** ☐ — no PR opened yet

**Verification transcripts attached for every named test:** ☑

### The defect this gate caught

Running the `secret-scan` job rather than assuming it — the whole point of a transcript deliverable —
**the job failed, on this change's own artifacts:**

```transcript
$ python3 vault_secrets.py --history .
HIGH (object database, incl. unreachable): 2 match(es)
  [private-key-block] tests/test_secret_scan.py:94  ----... (len=35)
  [private-key-block] vault-template/99-Operations/scripts/secret-scan-script.md:188  ----... (len=35)
$ grep -qE "^HIGH .*: 0 match" scan.out ; echo rc=$?
rc=1
```

**Cause.** Three of the four selftest fixtures were *constructed* (`b"ghp_" + b"A"*36`) precisely so
the scanner would not flag its own source. The private-key header was left as a **literal**, so the
scanner correctly detected its own pattern table and its own test module.

**Fix.** Build that fixture from parts too, in both files. **Rejected alternative:** excluding the
scanner's own paths from the scan — that carves a blind spot exactly where a real secret would be
most quietly hidden, and a detector with a self-shaped hole is the failure this change exists to
prevent.

**Consequence for the branch.** The literal is in the object database of the implementation commit,
and `main` merges by merge-commit rather than squash — so those blobs would enter `main`'s reachable
history and the job would fail there permanently. The branch was therefore **rebuilt before any push**
(local, unshared, three commits recreated with corrected content). Stated rather than done quietly:
the record of the defect lives here, in the gate that caught it, which is the durable place for it.

### Post-fix transcripts

```transcript
$ python3 vault_secrets.py --selftest
selftest: patterns fire, tiers are disjoint
rc=0
$ python3 vault_secrets.py --history .
HIGH (object database, incl. unreachable): 0 match(es)
rc=0
$ python3 vault_secrets.py tests vault-template .github
HIGH: 0 match(es)
ADVISORY (report-only, never gates): 2 match(es)
  [assignment-secretish] tests/test_secret_scan.py:119  hunt... (len=10)
  [assignment-secretish] vault-template/99-Operations/scripts/secret-scan-script.md:202  hunt... (len=10)
```

The two remaining hits are ADVISORY-tier `hunter2000` fixtures. They are **the tier that never
gates**, and their presence is the working demonstration of that separation.

**Proof that the rebuild actually removed the literal from what CI will see.** A local `--history`
scan is not the right instrument here: `--batch-all-objects` includes unreachable objects, so the
discarded pre-rebuild commits remain visible in the author's own clone until `gc`. CI does a fresh
`actions/checkout`, which fetches reachable history only. Simulated exactly that:

```transcript
$ git clone --no-local --branch feat/enforce-inv7-secret-scan <repo> ci-sim
$ cd ci-sim && git cat-file --batch-all-objects --batch-check='%(objecttype)' | sort | uniq -c
    889 blob
    198 commit
     31 tag
   1111 tree
$ python3 vault_secrets.py --history .
HIGH (object database, incl. unreachable): 0 match(es)
$ grep -qE "^HIGH .*: 0 match" ci.out ; echo rc=$?
rc=0
```

```transcript
$ python3 -m pytest tests/ -q
........................................................................ [ 94%]
....                                                                     [100%]
76 passed in 11.21s          # 63 prior + 13 new, no regressions
```

```transcript
$ node_modules/.bin/openspec validate --all
Totals: 8 passed, 0 failed (8 items)
rc=0

$ constitution-lint  (ci.yml inline, run verbatim)
constitution-lint: 6 specs carry protects:, 5 CONST entries, template present
rc=0

$ vocabulary-lint  (ci.yml inline, run verbatim)
config vars missing: none | grades=['bronze', 'coal', 'gold', 'silver'] match=True
rc=0

$ adr-count-lint  (ci.yml inline, run verbatim)
adr-count-lint OK: 36 ADRs, latest 0036
rc=0

$ link-check  (ci.yml inline, run verbatim)
link-check: 0 broken internal links
rc=0
```

```transcript
$ bash .github/scripts/validate-scripts.sh
== fresh-vault smoke ==
  ok    reconcile zero drift          # with 14 scripts
  ok    lint clean (empty treasury)
  ok    refine-detect empty
== INV-11 executor boundary ==
  ok    executor rejects non-kebab target_note, no Treasury write
  ok    executor applies conforming proposal
```

**Environment caveat, stated because the raw output looks like a failure and is not.** In the authoring
sandbox `validate-scripts.sh` reports `FAIL py_compile` / `FAIL bash -n` for **all** scripts, new and
pre-existing alike (`vault-dump.sh`, `vault-slag.sh`, `pre-commit`). Cause: the script writes its
diagnostics to hardcoded `/tmp/pc.txt` and `/tmp/bn.txt`, which the sandbox mounts read-only — the
*redirection* fails, not the check. Verified directly, without the redirect:

```transcript
$ python3 -m py_compile vault_secrets.py ; echo rc=$?
rc=0
$ bash -n pre-commit ; echo rc=$?
rc=0
```

The hardcoded `/tmp` paths are a genuine latent portability defect in `validate-scripts.sh`.
**Queued as its own change, deliberately not fixed here** — it is unrelated to INV-7 and folding it in
is the violation recorded as F29 in the live vault's failure-mode ledger.

### Phase-0 baseline (pre-change), instrument validated against a planted-secret control fixture first — live, deleted, and unreachable states all detected

| Repo | Blobs scanned | Working-tree files | HIGH | ADVISORY |
|---|---|---|---|---|
| Live vault | 610 | 209 | 0 | 0 |
| Framework repo | 889 | 339 | 0 | 0 |

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☐
**Gate-1 transcript re-run; output diffed clean against the proposal:** ☐

**Consequences explicitly accepted:**

> A format-shaped string that is not a credential can block a legitimate commit; the operator
> absorbs that cost in exchange for a Tier-0 invariant that fires. Every commit gains one
> subprocess. The scanner detects **known formats only** — a shapeless password, a split or
> encoded secret, or a novel vendor format passes. **A clean run is not proof of absence**, and
> must never be cited as one; custody discipline (keyring today, a manager if this ever goes
> multi-user) is the other half and is not delivered here.
>
> Forks inherit a gate that can block their commits. It is bypassable by the operator with
> `--no-verify`, deliberately: this gate protects against accident, not against its own operator.

**ADR created:** `openspec/adr/0036-enforce-inv7-secret-scan.md` ☐
**ADR captures:** context / options / choice / consequence / **sacrifice** ☐

**SIGN-OFF** (human only — agents may not sign):
Name: ___________________________
Date: ___________________________
