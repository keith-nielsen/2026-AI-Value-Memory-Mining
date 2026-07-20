#!/usr/bin/env python3
"""Template<->live parity check — is a deployed vault's LOCKSTEP scaffold in sync
with what this repo's `vault-template/` ships?

Orthogonal to render/reconcile. `reconcile` compares a script note to its deployed
`~/bin` target (note -> host). This compares the framework repo's shipped scaffold
(`vault-template/<prefix>`) against a deployed live vault (`<VAULT_ROOT>/<prefix>`) for
every LOCKSTEP prefix declared in `template-sync-manifest.json`. It answers the question
`reconcile` cannot: after a post-merge mirror, does every governed scaffold file the repo
shipped actually match what is deployed? Detection-only — it never writes; a human (or the
`template-mirror.py` driver) re-runs the mirror to resolve drift (same posture as reconcile /
INV-3).

Repo-only tool. The deployed vault is standalone (F15) and never references the repo, so
parity is a maintainer/mirror-time concern — not a vault fleet script, not a CI gate (CI
has no live vault to compare against). Stdlib-only, offline, no LLM (the INV-6 determinism
posture at the mirror-time layer). The tree-walk/comparison logic is shared with
`template-mirror.py` via `template_sync.py` — one source of truth for what "in sync" means.

Usage:  tools/template-parity.py [LIVE_VAULT]     # LIVE_VAULT defaults to $VAULT_ROOT
Exit:   0 in parity · 1 drift found · 3 blocked (no resolvable live vault / bad manifest).
"""
import pathlib
import sys

import template_sync as ts

EXIT_OK = 0
EXIT_DRIFT = 1


def main(argv):
    here = pathlib.Path(__file__).resolve().parent          # tools/
    template, live, prefixes, exclude = ts.resolve_trees(here, ts.live_arg_from(argv))

    checked, excluded, drift = ts.compare(template, live, prefixes, exclude)

    for rel, reason in drift:
        print(f"{reason}: {rel}")
    # Print the denominator, never a bare "clean": an empty drift list is only trustworthy
    # next to the count of files actually compared (F20 — evidence, not an unearned "ok").
    print(ts.tally_line(checked, prefixes, excluded, len(drift)))
    return EXIT_DRIFT if drift else EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
