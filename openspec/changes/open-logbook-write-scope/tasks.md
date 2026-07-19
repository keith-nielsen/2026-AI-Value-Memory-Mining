<!-- SPDX-License-Identifier: Apache-2.0 -->
# Tasks — open-logbook-write-scope

Exit criteria: `10-Logbook/` is agent-writable at both enforcement layers in the template and in the
deployed vault; the widening is recorded as a governed decision rather than a config diff; no other
area moves; CI green.

## 1. Governance artifacts

- [x] 1.1 ADR-0033 drafted (`openspec/adr/0033-open-logbook-write-scope.md`)
- [x] 1.2 Proposal drafted with an **executed** Gate-1 sweep
- [x] 1.3 `access-control` delta: MODIFY `Area Access Matrix` (row + footnote ⁷ + 1 new scenario,
      all 4 existing scenarios and the full table restated verbatim) and MODIFY
      `OS/Harness-Enforced Agent Write Scope` (silo leaves the denied set; +1 scenario requiring a
      governed change to open any protected area)
- [ ] 1.4 `openspec validate open-logbook-write-scope --strict` green — transcript below
- [ ] 1.5 `openspec validate --all --strict` green — transcript below

## 2. Template change

- [x] 2.1 `vault-template/.claude/settings.json` — remove `"./10-Logbook"` from
      `sandbox.filesystem.denyWrite`; **no tool-layer rule added**; verified by parsing the JSON
      (`denyWrite` 6 → 5, `deny` unchanged at 5, `allow`/`allowWrite`/`network` untouched)
- [x] 2.2 README ADR counts 32 → 33 in 3 places (`ls openspec/adr/*.md | wc -l` → 33)
- [ ] 2.3 `CHANGELOG.md` — `[Unreleased]` entry

## 3. Regression

- [ ] 3.1 `pytest` green
- [ ] 3.2 `validate-scripts.sh` green
- [ ] 3.3 Confirm no other area left either denied set — parse both settings files and enumerate
- [x] 3.4 **Naming decision recorded: option (a)** — INV-11 stays vault-wide, no Logbook carve-out
      (operator, 2026-07-19). **No change required**: naming lives in `vault_naming.py --check-strict`
      + the commit-gate, not in `settings.json`. Verified against the operator's expected patterns —
      `2026-07-19.md` exempt; `2026-07-19-whatever.md` and `effort-audit-trail.md` pass;
      `hermes-log.md`, `log.md`, `notes.md`, `Hermes_Log.md` all `INVALID … fewer than 3
      hyphen-tokens (INV-11 floor)`. **Note:** the first run of this check used `--check` and returned
      `rc=0` for every name including `log.md` — a mode structurally unable to fail (F20 shape);
      `--check-strict` is the mode that carries the floor (ADR-0030)
- [x] 3.5 Enforcement limits documented in ADR-0033 after reading the gate: commit-time only, `*.md`
      only (**non-Markdown in `10-Logbook/` is unchecked**), `--diff-filter=AR` only, bypassable via
      `--no-verify` / an unconfigured `core.hooksPath`

## 4. Live vault

- [x] 4.1 **Already in the target state** — the operator applied it before the template carried it.
      Legitimate because `.claude/settings.json` is SEED in `template-sync-manifest.json`
      (instance-owned, never parity-compared); this change moves the *policy* upstream so forks
      inherit it. **No mirror step required.**
- [x] 4.2 Live file re-verified: parses OK; `deny` 5 entries (no `10-Logbook/Daily`), `denyWrite` 5
      entries (no `./10-Logbook`), `excludedCommands` 1, `allow` 7, `network` 7 — nothing collateral
      lost
- [ ] 4.3 Post-merge: confirm template and live agree on the changed keys (they are SEED, so this is
      a coherence check, not a parity gate)

## 5. Ship

- [ ] 5.1 PR with the ```scope block in place **before** the push CI evaluates (F21#1); archive-time
      paths declared from the start
- [ ] 5.2 CI green
- [ ] 5.3 Gate-4 human sign-off (absolute proposal path + "reply Approved")
- [ ] 5.4 Archive — plain MODIFIED both Requirements, so the archiver's automatic path applies; **no
      `--skip-specs` override needed this time** (no scenario is removed or renamed)
- [ ] 5.5 Ship via `tools/ship-release.py v0.1.32` — stamp the CHANGELOG version heading **first**
      (the step CONTRIBUTING omits; it cost an extra PR in v0.1.31)
