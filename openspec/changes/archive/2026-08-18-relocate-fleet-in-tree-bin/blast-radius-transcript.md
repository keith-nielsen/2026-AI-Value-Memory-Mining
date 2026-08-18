<!-- SPDX-License-Identifier: Apache-2.0 -->
# Blast-radius transcript — relocate-fleet-in-tree-bin

Constitution §3 Gate 1 requires the blast radius as a **pasted, re-runnable command transcript**
— the exact command plus its full, untruncated output — never a list composed from reasoning.
Captured 2026-08-18. Re-run these commands verbatim at Gate 4 and diff against this file.

## Command 1 — every file in the corpus referencing a host bin path

```
$ cd "$FRAMEWORK_ROOT"
$ grep -rIlE '~/bin|\$HOME/bin|Path\.home\(\)' \
    openspec/ vault-template/ docs/ .github/ README.md AGENTS.md CONTRIBUTING.md | sort
```

```
AGENTS.md
docs/diagrams.md
docs/obsidian.md
docs/USING-THIS-TEMPLATE.md
.github/scripts/validate-scripts.sh
openspec/adr/0023-shared-vault-lib-plumbing.md
openspec/adr/0032-retire-daily-close-cycle.md
openspec/adr/0035-adopt-strict-write-scope-sandbox.md
openspec/adr/0036-enforce-inv7-secret-scan.md
openspec/changes/archive/2026-06-27-mold-naming/design.md
openspec/changes/archive/2026-06-27-mold-naming/tasks.md
openspec/changes/archive/2026-06-28-system-artifact-naming/design.md
openspec/changes/archive/2026-06-28-system-artifact-naming/proposal.md
openspec/changes/archive/2026-06-28-system-artifact-naming/specs/maintenance/spec.md
openspec/changes/archive/2026-06-29-private-by-default-publish-guard/specs/maintenance/spec.md
openspec/changes/archive/2026-07-02-naming-special-file-exemptions/specs/naming-rules/spec.md
openspec/changes/archive/2026-07-02-publication-boundary-manifest/specs/maintenance/spec.md
openspec/changes/archive/2026-07-05-add-shared-vault-lib/design.md
openspec/changes/archive/2026-07-05-add-shared-vault-lib/proposal.md
openspec/changes/archive/2026-07-05-add-shared-vault-lib/specs/maintenance/spec.md
openspec/changes/archive/2026-07-05-add-shared-vault-lib/tasks.md
openspec/changes/archive/2026-07-06-bank-execute-pre-flight/specs/maintenance/spec.md
openspec/changes/archive/2026-07-06-commit-ownership-de-sweep/specs/maintenance/spec.md
openspec/changes/archive/2026-07-06-commit-ownership-de-sweep/tasks.md
openspec/changes/archive/2026-07-06-fix-commit-gate-env-guard/proposal.md
openspec/changes/archive/2026-07-06-fix-commit-gate-env-guard/specs/maintenance/spec.md
openspec/changes/archive/2026-07-06-reconcile-fence-lint-guard-inventory/specs/maintenance/spec.md
openspec/changes/archive/2026-07-06-shell-pair-conformance/specs/maintenance/spec.md
openspec/changes/archive/2026-07-06-wave-2-vault-lib-adoption/proposal.md
openspec/changes/archive/2026-07-06-wave-2-vault-lib-adoption/specs/maintenance/spec.md
openspec/changes/archive/2026-07-06-wave-2-vault-lib-adoption/tasks.md
openspec/changes/archive/2026-07-13-bank-execute-pending-catalog/proposal.md
openspec/changes/archive/2026-07-13-bank-execute-pending-catalog/specs/maintenance/spec.md
openspec/changes/archive/2026-07-13-bank-execute-pending-catalog/tasks.md
openspec/changes/archive/2026-07-13-os-enforced-agent-write-scope/design.md
openspec/changes/archive/2026-07-13-os-enforced-agent-write-scope/proposal.md
openspec/changes/archive/2026-07-13-os-enforced-agent-write-scope/specs/access-control/spec.md
openspec/changes/archive/2026-07-17-enforce-naming-token-floor/tasks.md
openspec/changes/archive/2026-07-17-enforce-pillar-slug-tokens/tasks.md
openspec/changes/archive/2026-07-17-retire-effort-projections/proposal.md
openspec/changes/archive/2026-07-17-retire-effort-projections/specs/access-control/spec.md
openspec/changes/archive/2026-07-17-retire-effort-projections/specs/maintenance/spec.md
openspec/changes/archive/2026-07-17-retire-effort-projections/tasks.md
openspec/changes/archive/2026-07-18-add-template-parity-check/proposal.md
openspec/changes/archive/2026-07-18-add-template-parity-check/specs/maintenance/spec.md
openspec/changes/archive/2026-07-18-add-template-parity-check/tasks.md
openspec/changes/archive/2026-07-18-fix-append-idempotent-catalog-link/proposal.md
openspec/changes/archive/2026-07-18-fix-append-idempotent-catalog-link/tasks.md
openspec/changes/archive/2026-07-19-fix-operator-only-path-diagnostics/proposal.md
openspec/changes/archive/2026-07-19-fix-operator-only-path-diagnostics/specs/maintenance/spec.md
openspec/changes/archive/2026-07-19-fix-operator-only-path-diagnostics/tasks.md
openspec/changes/archive/2026-07-19-open-logbook-write-scope/specs/access-control/spec.md
openspec/changes/archive/2026-07-19-retire-daily-close-cycle/proposal.md
openspec/changes/archive/2026-07-19-retire-daily-close-cycle/specs/access-control/spec.md
openspec/changes/archive/2026-07-19-retire-daily-close-cycle/specs/maintenance/spec.md
openspec/changes/archive/2026-07-19-retire-daily-close-cycle/tasks.md
openspec/changes/archive/2026-07-28-enforce-inv7-secret-scan/proposal.md
openspec/changes/archive/2026-07-28-enforce-inv7-secret-scan/specs/access-control/spec.md
openspec/changes/archive/2026-07-28-enforce-inv7-secret-scan/tasks.md
openspec/changes/archive/2026-08-17-emission-record-downgrades-ask/tasks.md
openspec/changes/archive/2026-08-17-probe-vocabulary-and-json/tasks.md
openspec/changes/archive/add-naming-rules/tasks.md
openspec/changes/relocate-fleet-in-tree-bin/baseline-preflight-record.md
openspec/changes/relocate-fleet-in-tree-bin/blast-radius-transcript.md
openspec/changes/relocate-fleet-in-tree-bin/proposal.md
openspec/changes/relocate-fleet-in-tree-bin/tasks.md
openspec/specs/access-control/spec.md
openspec/specs/maintenance/spec.md
openspec/specs/naming-rules/spec.md
README.md
vault-template/00-Docs/README.md
vault-template/96-Runbooks/refine-pipeline-runbook.md
vault-template/96-Runbooks/render-reconcile-runbook.md
vault-template/99-Operations/scripts/bank-execute-script.md
vault-template/99-Operations/scripts/knowledge-lint-script.md
vault-template/99-Operations/scripts/naming-rules-script.md
vault-template/99-Operations/scripts/ore-detect-script.md
vault-template/99-Operations/scripts/render-reconcile-script.md
vault-template/99-Operations/scripts/secret-scan-script.md
vault-template/99-Operations/scripts/site-slag-script.md
vault-template/99-Operations/scripts/spoil-dump-script.md
vault-template/99-Operations/scripts/tailings-reprospect-script.md
vault-template/99-Operations/scripts/treasury-orphan-script.md
vault-template/99-Operations/scripts/vault-lib-script.md
vault-template/.claude/settings.json
```

## Command 2 — the FROZEN partition (archived record; must NOT be edited)

```
$ grep -rIlE '~/bin|\$HOME/bin|Path\.home\(\)' openspec/changes/archive/ | wc -l
53
$ grep -rIlE '~/bin|\$HOME/bin' "$VAULT_ROOT"/30-Sites "$VAULT_ROOT"/71-Spoil "$VAULT_ROOT"/20-Claims "$VAULT_ROOT"/10-Logbook | wc -l
19
$ grep -cE '~/bin|\$HOME/bin' CHANGELOG.md
8
```

## Command 3 — LIVE surface, line level (this is what the change edits)

```
$ grep -rInE '~/bin|\$HOME/bin|Path\.home\(\)' \
    openspec/specs/ vault-template/ docs/ .github/ README.md AGENTS.md CONTRIBUTING.md tools/ tests/
```

```
AGENTS.md:189:  note → `~/bin`, not template → live).
AGENTS.md:98:invocation** (e.g. `~/bin/vault-refine-execute.py`) — that form is sandbox-excluded so the script can
AGENTS.md:99:write what it owns. An interpreter-prefixed (`python3 ~/bin/…`), chained, or relative invocation runs
docs/diagrams.md:311:    HOST>~/bin/vault-*.py<br/>deployed artifacts]:::infra
docs/obsidian.md:104:flatpak-spawn --host bash -lc '. ~/Documents/Vault/99-Operations/config.env && python3 ~/bin/vault-lint.py'
docs/obsidian.md:94:A Flatpak sandbox can't see the host `python3` + `frontmatter` or `~/bin`, so you must
docs/USING-THIS-TEMPLATE.md:134:target = pathlib.Path(os.path.expanduser("~/bin/vault-render.py"))
docs/USING-THIS-TEMPLATE.md:141:python3 ~/bin/vault-render.py render
docs/USING-THIS-TEMPLATE.md:142:python3 ~/bin/vault_naming.py
docs/USING-THIS-TEMPLATE.md:143:python3 ~/bin/vault-render.py reconcile
docs/USING-THIS-TEMPLATE.md:231:python3 ~/bin/vault-refine-detect.py   # when you are about to refine
docs/USING-THIS-TEMPLATE.md:232:python3 ~/bin/vault-render.py reconcile  # when a script note changed
docs/USING-THIS-TEMPLATE.md:266:| `~/bin` location | Change `deploy_target` values in script notes if you use a different local bin path |
docs/USING-THIS-TEMPLATE.md:304:| Lint the vault | `python3 ~/bin/vault-lint.py` |
docs/USING-THIS-TEMPLATE.md:305:| Find orphaned Treasury notes | `python3 ~/bin/vault-orphans.py` |
docs/USING-THIS-TEMPLATE.md:308:| Re-prospect Tailings | `python3 ~/bin/vault-reprospect.py` |
docs/USING-THIS-TEMPLATE.md:309:| Check for drift | `python3 ~/bin/vault-render.py reconcile` |
docs/USING-THIS-TEMPLATE.md:310:| Re-deploy after source edit | `python3 ~/bin/vault-render.py render` |
.github/scripts/validate-scripts.sh:13:mkdir -p "$HOME/bin"
.github/scripts/validate-scripts.sh:40:out = pathlib.Path(os.path.expanduser("~/bin/vault-render.py"))
.github/scripts/validate-scripts.sh:43:python3 "$HOME/bin/vault-render.py" render >/dev/null || { no "render failed"; exit 2; }
.github/scripts/validate-scripts.sh:44:python3 "$HOME/bin/vault_naming.py" >/dev/null
.github/scripts/validate-scripts.sh:67:python3 "$HOME/bin/vault-render.py" reconcile >/dev/null && ok "reconcile zero drift" || no "reconcile drift"
.github/scripts/validate-scripts.sh:69:lint_out=$(python3 "$HOME/bin/vault-lint.py" 2>&1); lint_rc=$?
.github/scripts/validate-scripts.sh:72:python3 "$HOME/bin/vault-refine-detect.py" | grep -q "queued 0" && ok "refine-detect empty" || no "refine-detect"
.github/scripts/validate-scripts.sh:82:out=$(python3 "$HOME/bin/vault-refine-execute.py" 2>&1)
.github/scripts/validate-scripts.sh:96:python3 "$HOME/bin/vault-refine-execute.py" >/dev/null 2>&1
openspec/specs/access-control/spec.md:305:  `~/bin/vault-refine-execute.py`)
openspec/specs/access-control/spec.md:319:A credential-format scanner (`~/bin/vault_secrets.py`, rendered from
openspec/specs/maintenance/spec.md:104:| `render-reconcile-script.md` | `~/bin/vault-render.py` | manual | Deploy Layer-0 code blocks to host targets; detect drift |
openspec/specs/maintenance/spec.md:105:| `knowledge-lint-script.md` | `~/bin/vault-lint.py` | manual / pre-commit | Validate Treasury frontmatter and name conformance |
openspec/specs/maintenance/spec.md:106:| `treasury-orphan-script.md` | `~/bin/vault-orphans.py` | manual / weekly | Report Treasury notes not linked from any Catalog index |
openspec/specs/maintenance/spec.md:107:| `ore-detect-script.md` | `~/bin/vault-refine-detect.py` | manual | Queue ore whose grade cleared the Sort gate |
openspec/specs/maintenance/spec.md:108:| `bank-execute-script.md` | `~/bin/vault-refine-execute.py` | manual | Apply approved proposals from `_refine-approved/`; writes Treasury; one atomic commit per banked proposal (`bank: <stem>`) |
openspec/specs/maintenance/spec.md:109:| `spoil-dump-script.md` | `~/bin/vault-dump.sh` | manual | Move a spent husk to `71-Spoil/`; one commit |
openspec/specs/maintenance/spec.md:110:| `site-slag-script.md` | `~/bin/vault-slag.sh` | manual | Move an uneconomic effort to `70-Tailings/`; one commit |
openspec/specs/maintenance/spec.md:111:| `tailings-reprospect-script.md` | `~/bin/vault-reprospect.py` | manual | List slagged efforts for re-evaluation; detection only |
openspec/specs/maintenance/spec.md:112:| `naming-rules-script.md` | `~/bin/vault_naming.py` | manual | Naming validator SSOT; also emits `naming-rules.json` |
openspec/specs/maintenance/spec.md:113:| `vault-lib-script.md` | `~/bin/vault_lib.py` | manual | Shared fleet plumbing: root resolution, config vocabulary, frontmatter access, scoped one-commit helper, fleet exit-code contract (ADR-0023) |
openspec/specs/maintenance/spec.md:131:Sibling scripts import the shared modules (`vault_naming`, `vault_lib`) from `~/bin` via
openspec/specs/maintenance/spec.md:132:`sys.path.insert(0, str(pathlib.Path.home() / "bin"))`; the underscore module names mark
openspec/specs/maintenance/spec.md:197:  `~/bin/vault-refine-detect.py`) from a shell with no `VAULT_ROOT` set, cwd inside the vault
openspec/specs/maintenance/spec.md:240:sole automated writer of `40-Treasury/` (`bank-execute-script` → `~/bin/vault-refine-execute.py`),
openspec/specs/maintenance/spec.md:528:cannot: `reconcile` compares a script note to its deployed `~/bin` target (note → host); this
openspec/specs/maintenance/spec.md:726:`deploy_target`s (`~/bin/`, `99-Operations/hooks/`, `.claude/hooks/`) and `vault_naming.py` in emit
openspec/specs/naming-rules/spec.md:103:- **WHEN** `python3 ~/bin/vault_naming.py` is run with no arguments
README.md:200:target = pathlib.Path(os.path.expanduser("~/bin/vault-render.py"))
README.md:205:python3 ~/bin/vault-render.py render
README.md:206:python3 ~/bin/vault_naming.py                        # emit naming-rules.json
README.md:222:`vault-template/99-Operations/scripts/` and deployed to `~/bin/` via `render`.
tools/pr-flow.py:363:                 pathlib.Path.home() / ".claude/hooks/outbound-publish-guard.py"):
vault-template/00-Docs/README.md:107:out = pathlib.Path(os.path.expanduser("~/bin/vault-render.py"))
vault-template/00-Docs/README.md:112:python3 ~/bin/vault-render.py render               # deploy all scripts
vault-template/00-Docs/README.md:113:python3 ~/bin/vault_naming.py                      # emit naming-rules.json
vault-template/00-Docs/README.md:129:python3 ~/bin/vault-render.py reconcile
vault-template/00-Docs/README.md:141:python3 ~/bin/vault-seed.py       # populate with example efforts
vault-template/00-Docs/README.md:142:python3 ~/bin/vault-cleanup.py    # remove example data
vault-template/96-Runbooks/refine-pipeline-runbook.md:26:1. `[script]` `~/bin/vault-refine-detect.py` — writes the queue to
vault-template/96-Runbooks/refine-pipeline-runbook.md:35:4. `[script]` `~/bin/vault-refine-execute.py` — pre-flights each proposal whole (schema,
vault-template/96-Runbooks/refine-pipeline-runbook.md:39:5. `[human]` Dispose the husk: verify the Treasury entry, then `~/bin/vault-dump.sh <slug>`
vault-template/96-Runbooks/refine-pipeline-runbook.md:40:   (→ `71-Spoil/`) — or `~/bin/vault-slag.sh <slug>` if the effort was uneconomic instead.
vault-template/96-Runbooks/refine-pipeline-runbook.md:57:- `~/bin/vault-lint.py` exits 0; `~/bin/vault-orphans.py` reports no new orphan.
vault-template/96-Runbooks/render-reconcile-runbook.md:21:- `[script]` `~/bin/vault-render.py` present (bootstrap: extract its code fence from
vault-template/96-Runbooks/render-reconcile-runbook.md:30:2. `[script]` `~/bin/vault-render.py render` — deploys all notes; `chmod +x` applied. **Wholly
vault-template/96-Runbooks/render-reconcile-runbook.md:32:   `99-Operations/hooks/`.** `~/bin/` is out-of-vault and default-denied, so a sandboxed agent
vault-template/96-Runbooks/render-reconcile-runbook.md:36:3. `[script]` `~/bin/vault-render.py reconcile` — expect `ok:` for every note, exit 0.
vault-template/96-Runbooks/render-reconcile-runbook.md:51:- `~/bin/vault-render.py reconcile` exits 0 with `ok:` for all notes (17 at last validation).
vault-template/99-Operations/scripts/bank-execute-script.md:34:sys.path.insert(0, str(pathlib.Path.home() / "bin"))
vault-template/99-Operations/scripts/bank-execute-script.md:3:deploy_target: ~/bin/vault-refine-execute.py
vault-template/99-Operations/scripts/knowledge-lint-script.md:12:Imports the shared naming validator (naming.md → `~/bin/vault_naming.py`) so
vault-template/99-Operations/scripts/knowledge-lint-script.md:37:sys.path.insert(0, str(pathlib.Path.home() / "bin"))
vault-template/99-Operations/scripts/knowledge-lint-script.md:3:deploy_target: ~/bin/vault-lint.py
vault-template/99-Operations/scripts/naming-rules-script.md:3:deploy_target: ~/bin/vault_naming.py
vault-template/99-Operations/scripts/ore-detect-script.md:27:sys.path.insert(0, str(pathlib.Path.home() / "bin"))
vault-template/99-Operations/scripts/ore-detect-script.md:3:deploy_target: ~/bin/vault-refine-detect.py
vault-template/99-Operations/scripts/render-reconcile-script.md:3:deploy_target: ~/bin/vault-render.py
vault-template/99-Operations/scripts/render-reconcile-script.md:66:            # Area Access Matrix withholds from the agent (~/bin is out-of-vault;
vault-template/99-Operations/scripts/secret-scan-script.md:3:deploy_target: ~/bin/vault_secrets.py
vault-template/99-Operations/scripts/site-slag-script.md:3:deploy_target: ~/bin/vault-slag.sh
vault-template/99-Operations/scripts/spoil-dump-script.md:3:deploy_target: ~/bin/vault-dump.sh
vault-template/99-Operations/scripts/tailings-reprospect-script.md:22:sys.path.insert(0, str(pathlib.Path.home() / "bin"))
vault-template/99-Operations/scripts/tailings-reprospect-script.md:3:deploy_target: ~/bin/vault-reprospect.py
vault-template/99-Operations/scripts/treasury-orphan-script.md:20:sys.path.insert(0, str(pathlib.Path.home() / "bin"))
vault-template/99-Operations/scripts/treasury-orphan-script.md:3:deploy_target: ~/bin/vault-orphans.py
vault-template/99-Operations/scripts/vault-lib-script.md:25:`vault_naming`: `sys.path.insert(0, str(pathlib.Path.home() / "bin"))`. The `frontmatter` import is
vault-template/99-Operations/scripts/vault-lib-script.md:3:deploy_target: ~/bin/vault_lib.py
vault-template/.claude/settings.json:23:      "~/bin/vault-refine-execute.py *"
```

## Command 4 — the five hardcoded `$HOME` imports (source-level dependency)

```
$ grep -rn 'Path.home() / "bin"' vault-template/99-Operations/scripts/
```

```
vault-template/99-Operations/scripts/treasury-orphan-script.md:20:sys.path.insert(0, str(pathlib.Path.home() / "bin"))
vault-template/99-Operations/scripts/bank-execute-script.md:34:sys.path.insert(0, str(pathlib.Path.home() / "bin"))
vault-template/99-Operations/scripts/ore-detect-script.md:27:sys.path.insert(0, str(pathlib.Path.home() / "bin"))
vault-template/99-Operations/scripts/knowledge-lint-script.md:37:sys.path.insert(0, str(pathlib.Path.home() / "bin"))
vault-template/99-Operations/scripts/vault-lib-script.md:25:`vault_naming`: `sys.path.insert(0, str(pathlib.Path.home() / "bin"))`. The `frontmatter` import is
vault-template/99-Operations/scripts/tailings-reprospect-script.md:22:sys.path.insert(0, str(pathlib.Path.home() / "bin"))
```

## Command 5 — note → deploy_target, the authoritative partition (11 host / 3 in-tree)

```
$ for f in vault-template/99-Operations/scripts/*.md; do
    printf "%-40s %s\n" "$(basename "$f")" "$(grep -m1 ^deploy_target: "$f" | cut -d" " -f2-)"
  done
```

```
bank-execute-script.md                   ~/bin/vault-refine-execute.py
commit-gate-script.md                    99-Operations/hooks/pre-commit
knowledge-lint-script.md                 ~/bin/vault-lint.py
naming-rules-script.md                   ~/bin/vault_naming.py
ore-detect-script.md                     ~/bin/vault-refine-detect.py
outbound-publish-guard-script.md         .claude/hooks/outbound-publish-guard.py
push-guard-script.md                     99-Operations/hooks/pre-push
render-reconcile-script.md               ~/bin/vault-render.py
secret-scan-script.md                    ~/bin/vault_secrets.py
site-slag-script.md                      ~/bin/vault-slag.sh
spoil-dump-script.md                     ~/bin/vault-dump.sh
tailings-reprospect-script.md            ~/bin/vault-reprospect.py
treasury-orphan-script.md                ~/bin/vault-orphans.py
vault-lib-script.md                      ~/bin/vault_lib.py
```

## Tally

| Partition | Files |
|---|---|
| corpus total (Command 1) | 85 |
| FROZEN — `openspec/changes/archive/` | 53 |
| FROZEN — vault dig record | 19 |
| LIVE — editable by this change | 25 |
