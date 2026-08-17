<!-- SPDX-License-Identifier: Apache-2.0 -->
# GATE A1 evidence — red before green

**Captured 2026-08-18.** Every check below was run on the **unmodified** tree and its failure
pasted. A check that passes before and after proves nothing about the change; a check never observed
refusing is an assumption.

Suite totals: baseline **328 passed** → **344 collected** (16 new: 7 inventory, 3 settings, 6 fleet).
Current state **339 passed, 5 failed** — the 5 failures are the intended red, cleared in A2.

---

## A1.1 — maintenance Script Inventory vs the note set

```
$ ~/ai-env/bin/python3 -m pytest tests/test_inventory_conformance.py -q
FAILED test_maintenance_spec_inventory_names_exactly_the_note_set
E   AssertionError: 1 script note(s) exist but have NO row in the maintenance Script
E   Inventory: ['secret-scan-script.md']. A shipped script absent from the spec that
E   governs it is the seam this test exists to close.
```

**RED confirmed.** Matches baseline §A0.3a exactly: 13 rows, 14 notes, `secret-scan` absent.

## A1.2 — README inventory and its stated count

```
FAILED test_readme_inventory_names_exactly_the_note_set
E   AssertionError: 4 deployed artifact(s) missing from the README table:
E   ['outbound-publish-guard.py', 'pre-push', 'vault_lib.py', 'vault_secrets.py']

FAILED test_readme_stated_count_equals_its_own_rows
E   AssertionError: README heading states 13 operational scripts; its own table presents 10 rows
```

**RED confirmed**, naming the same four artifacts predicted at A0.3b — derived independently by the
test from `deploy_target` frontmatter, not copied from the baseline.

## A1.4 — cadence conformance

```
FAILED test_no_live_document_states_a_cron_schedule
E   AssertionError: live document(s) state a schedule for a script whose note declares no
E   cron runtime; `render` deploys code and marks it executable, it installs no schedules:
E     README.md:231: | `vault-refine-detect.py` | `[script]` | `0 6 * * *` | Queue ore ...

FAILED test_no_document_instructs_editing_the_schedule_field
E   AssertionError: document(s) instruct editing a `schedule:` field that nothing reads:
E     docs/USING-THIS-TEMPLATE.md:264: | Cron schedules | Edit the `schedule:` field ...
```

**RED confirmed.** `test_no_note_declares_a_cron_runtime_or_schedule` **passes** — correctly, since
no note declares one. That is the premise the two failing tests rest on, asserted rather than assumed.

## A1.3 — settings path resolution ⚠ MANUFACTURED RED

**This check cannot fail naturally: the tree is correct.** Its red state was manufactured, observed,
and reverted. All three runs are recorded, because a check that has only ever been seen to pass is
not evidence.

```
######## RUN 1 — unmodified tree ########
3 passed in 0.01s                      <- proves nothing on its own

######## MANUFACTURE ########
patched vault-template/.claude/settings.json
  .sandbox.excludedCommands[0] -> '~/bin/does-not-exist.py *'

######## RUN 2 — manufactured red ########
E   AssertionError: 1 settings path(s) name an artifact that no script note deploys. An
E   exclusion is an exact string match: when its artifact moves, the entry does not error,
E   it stops matching, and the refusal is indistinguishable from a real deny.
E     vault-template/.claude/settings.json at .sandbox.excludedCommands[0]: '~/bin/does-not-exist.py'
1 failed, 2 passed in 0.03s

######## REVERT ########
$ git status --porcelain vault-template/.claude/settings.json
(empty — byte-identical to HEAD)

######## RUN 3 — post-revert ########
3 passed in 0.01s
```

The failure names the **exact JSON location**, not merely that something is wrong. A guard that
reports only its verdict makes the reader derive the cause at the moment they have already shown they
cannot.

**Change B is the first change in this repository's history that can trip this check naturally.**

## A1.5 / A1.6 — behavioural coverage, and proof of non-vacuity

No test existed for either script: recorded as **absent**, never as a passing run. Six new tests pass
immediately — which on its own proves nothing, so both scripts were **mutated** to confirm the tests
can fail.

```
=== MUTATION 1: treasury-orphan never reports an orphan ===
  orphans = [p.stem for p in (vault / "40-Treasury").glob("*.md") if False]
FAILED test_orphan_reports_a_treasury_note_no_index_links
1 failed, 2 passed

=== MUTATION 2: reprospect enumerates nothing ===
  for idx in (p for p in (vault / "70-Tailings").glob("*/NOTHING.md") ...)
FAILED test_reprospect_lists_a_slagged_effort_with_its_metadata
FAILED test_reprospect_ignores_a_non_index_note_in_a_slagged_folder
2 failed, 1 passed

=== REVERT ===
$ git status --porcelain vault-template/99-Operations/scripts/
(empty — clean)

=== post-revert ===
6 passed
```

Each script also carries a **confirming-half** test, so a script that reported *everything* would not
pass: `test_orphan_does_not_report_a_catalog_linked_note` and
`test_reprospect_ignores_a_non_index_note_in_a_slagged_folder`. And each carries a
**detection-only** assertion — commit count unchanged and working tree clean — because for a tool
whose correct behaviour is to report, a silent no-op and a correct report are indistinguishable from
an exit code alone.

---

## Guards on the guards

Three tests exist solely so the others cannot pass vacuously:

| Test | Prevents |
|---|---|
| `test_ground_truth_is_discoverable` (inventory) | an unreadable note set making every comparison trivially true |
| `test_ground_truth_is_discoverable` (settings) | an empty deploy-target set making resolution trivially true |
| `test_at_least_one_settings_file_declares_a_script_path` | a settings file that names nothing passing the resolution test |

Ground truth is read from disk in every case. No test carries a literal list of fleet members — that
would be one more hand-maintained duplicate of a machine-checkable fact, drifting exactly as the
enumerations it checks did.
