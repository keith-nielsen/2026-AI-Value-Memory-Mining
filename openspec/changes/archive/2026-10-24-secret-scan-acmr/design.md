# Design

## Context

See proposal.md, Why. The scanner lists staged paths with `git diff --cached --name-only`, then
reads each blob by its staged path. For a rename, `--name-only` prints the new path, so adding `R` to
the filter is enough: the blob read (`git show :<path>`) needs no change.

## Goals / Non-Goals

**Goals:** a renamed file's staged content is scanned like any other staged file.

**Non-Goals:** copy detection (`C` only appears with `-C`, which the gate does not pass); the
INV-11 naming half, which stays at `AR`; the history scan, which already reads every object.

## Decisions

- **Widen the filter rather than disable rename detection** (`--no-renames`). With renames off, a
  move shows as `D` plus `A` and the `A` side would be scanned too. But that depends on a flag every
  future edit must remember, and `ACMR` states the intent in the filter itself.
- **Do not drop the filter altogether.** Without it, `D` paths would be listed, and `git show` on a
  deleted path fails. Excluding `D`, `T`, `U`, `X` and `B` keeps the read well defined.
- **Test drives the deployed gate,** like its neighbours, and checks first that git really stages
  the move as `R`. Without that precondition the test could pass for the wrong reason (a `D` + `A`
  that `ACM` already caught).

## Risks / Trade-offs

- [A pure rename of a file holding a credential now blocks] → this is "never grandfathered" applied
  consistently. Measured exposure today is 0 HIGH matches in both trees, and `--no-verify` remains
  the operator's override, as ADR-0036 records.
