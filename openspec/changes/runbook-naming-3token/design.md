## Context

ADR-0015 ratified the ≥3-token / `silo-section-descriptor` rule; ADR-0016 conformed scripts, schemas,
and indexes. The two original runbooks (`close-daily`, `seal-provenance`) are the last grandfathered
2-token system-artifact names. They also anchor a three-way vocabulary drift: the script is already
`daily-close-script`, `session-bootstrap-loader` already says `daily-close`, but `AGENTS.md` and the
specs still say `close-daily`.

## Goals / Non-Goals

**Goals:** rename the two runbook files to the convention; unify the ritual vocabulary on one stem
family per ritual (`daily-close*`, `provenance-seal*`); sync the two spec deltas; repoint all
references.

**Non-Goals:** renaming `session-bootstrap-loader` (already conforms — out of scope to avoid extra
blast radius); `.py`/`.sh` binary renames (runbooks have no deploy target anyway); mechanical
enforcement of the ≥3 floor (separate deferred change).

## Decisions

- **Option A — unify on `daily-close` / `provenance-seal`** (chosen). Process, runbook file, and
  script share one stem family. Ends the drift; coheres with the already-renamed `daily-close-script`
  and the `session-bootstrap-loader` cross-ref that already reads `daily-close`.
  - *Option B (runbook files only)* rejected: leaves the ritual vocabulary divergent from the script
    and runbook — three names for one concept persists.
  - *Option C (keep `close-daily` order, add `-runbook`)* rejected: `close-daily-runbook` vs
    `daily-close-script` keeps the ordering mismatch.
- **Runbook stem = ritual stem + `-runbook` descriptor** (`daily-close-runbook`), and `id:` matches
  the filename (as `session-bootstrap-loader` does). The bare `daily-close` denotes the *process*.
- **`session-bootstrap-loader` unchanged** — already ≥3-token; renaming it would pull a third runbook
  into the blast radius for no naming gain.
- **History left intact** — ADR-0012, CHANGELOG, and archived changes name the runbooks as they were
  then (same policy as ADR-0016).

## Risks / Trade-offs

- Ritual-vocabulary rename touches two `protects:`-tagged specs → full constitution-override ceremony
  (this change), even though it is conforming. Accepted: same shape as ADR-0016.
- Missed reference → residual-name grep gate (`close-daily` / `seal-provenance`) before commit, scoped
  to exclude `openspec/changes/archive/`, ADR history, and CHANGELOG.
- No deploy/render impact — runbooks are read-and-follow procedure notes with no host binary.

## Migration Plan

`git mv` both runbooks (+ `id`/title/heading) → repoint references → apply spec deltas → Gate-4
sign-off → ADR-0017 → archive (sync specs) + CHANGELOG `[0.1.12]` + tag `v0.1.12` → mirror to live
vault (rename runbooks + repoint references; no re-render).

## Open Questions

- None blocking. Mechanical enforcement of the ≥3 floor remains a separate later change.
