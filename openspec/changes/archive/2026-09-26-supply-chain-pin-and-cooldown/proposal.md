<!-- SPDX-License-Identifier: Apache-2.0 -->
# Change: supply-chain-pin-and-cooldown

## Why

Two supply-chain exposures, both measured on 2026-09-25:

1. **Every GitHub Action is referenced by a mutable tag.** All 25 `uses:` lines (17 `actions/checkout`,
   3 `setup-node`, 5 `setup-python`) named `@v7`. A major tag is a moving pointer *by design*, and the
   tj-actions compromise (March 2025, CVE-2025-30066) worked by re-pointing existing tags: every
   consumer ran the attacker's code at its next run, with no update, PR or review in between. A cooldown
   cannot help there — nothing new is released. Only an immutable reference does.
2. **The update cooldown is a default this repository does not own.** `dependabot.yml` declared none.
   Since 2026-07-14 GitHub applies a 3-day cooldown when none is declared — so the policy existed, but
   as someone else's setting, changeable without any event here, and at the value (3 days) the published
   evidence rates weakest.

## What Changes

- **Pin every action to a full 40-hex commit SHA with a `# vX.Y.Z` comment.** The SHAs are the commits
  the `@v7` tags resolved to on 2026-09-25 (`git ls-remote`; lightweight tags, so the SHA is the
  commit), so behaviour is unchanged:
  `actions/checkout` v7.0.1 `3d3c42e5…`, `actions/setup-node` v7.0.0 `82076278…`,
  `actions/setup-python` v7.0.0 `5fda3b95…`. First-party `actions/*` are pinned too.
- **Declare the cooldown per ecosystem:** npm **14** days, github-actions and pip **7**.
- **npm schedule weekly → monthly** (OpenSpec releases ~weekly and is not chased).
- **Group GitHub Actions updates into one PR**, so SHA pins move together and are reviewed together.
- **Enforce both** with `tests/test_supply_chain_pins.py` (stdlib, offline, INV-6): every `uses:` is a
  SHA pin carrying a version comment; every ecosystem declares its cooldown at the policy value.
- **Spec:** `maintenance` ADDED *"Supply-Chain Inputs Are Pinned Immutably And Adopted After A
  Cooldown"*, beside the existing *"Governance Tooling Is Pinned…"* requirement.

## Evidence and design decisions

**Survey, 2026-09-25** — the real config files of 19 security-mature projects using GitHub Actions
(Kubernetes excluded: it runs Prow). Measured per `uses:` line.

- **SHA pinning incl. first-party `actions/*`:** 14 of 17 pinners — pypa/pip, python/cpython,
  electron, github/docs, microsoft/vscode, cli/cli, astral-sh/uv, nodejs/node, pnpm, renovate,
  ossf/scorecard, sigstore/cosign, vercel/next.js, home-assistant/core. Partial: grafana (third-party
  only), step-security/harden-runner. Tags only, trusting GitHub-owned actions: npm/cli, django,
  actions/checkout.
- **Comment format:** full version `# v7.0.1` is dominant; Dependabot rewrites it with the SHA. A
  major-only `# v4` goes stale.
- **Legitimately unpinned elsewhere:** same-repo local actions/reusable workflows, own-org actions, and
  the SLSA generator (it *requires* a tag ref). **None apply here** — all 25 are pinned.
- **Cooldowns declared:** 3 (cli/cli), 5 per semver (node), **7** (electron, docs, vscode, pnpm, pip;
  grafana and home-assistant via Renovate), 14 (cpython, citing Woodruff). No project uses 30 for npm.
- **Why these values:** Woodruff's analysis of ten 2024–25 supply-chain attacks — 3 days blocks 7,
  **7 blocks 8, 14 blocks 9**; the tenth (xz-utils, ~5 weeks dwell) is out of reach of any practical
  cooldown. Operator decision 2026-09-25: npm 14, the rest 7.
- **npm cooldown cannot starve a weekly release cadence** — verified in dependabot-core's npm
  `latest_version_finder.rb`: `filter_by_cooldown(possible_releases)` drops in-window releases and
  proposes the newest release older than the window. (GitHub Actions had the starvation bug —
  dependabot-core #14579 — fixed by #14621 on 2026-04-09.)
- **Enforcement choice:** a stdlib pytest, not zizmor. zizmor is broader and widely used (cli/cli, uv,
  pnpm, electron, cpython, …) but is a new third-party tool, against the trust-ring minimisation rule;
  the pytest covers exactly the two properties this change introduces.

## Out of scope — flagged, not done

- `persist-credentials: false` on checkout (most surveyed projects set it; 0 of our 17 checkouts do).
- The repository-level **"require SHA pinning"** Actions policy (GitHub, 2025-08-15) — a settings change,
  the operator's; it would make the pin rule server-enforced rather than test-enforced.
- The **canary** installs `@fission-ai/openspec@latest` with install scripts enabled — by design it
  takes day-0 releases, the exposure a cooldown avoids. Its token is `contents: read` with no secrets.
- npm's own `min-release-age` (npm ≥ 11.10); local npm is 10.9.8, and `npm ci` from a lockfile does not
  resolve versions, so CI gains nothing from it.

## Impact

- No behaviour change in CI: each SHA is exactly what its tag resolved to.
- Dependabot opens fewer, older-by-design PRs: Actions grouped monthly; npm monthly and ≥ 14 days old.
  PR #122 (OpenSpec 1.13.1, published 2026-09-17) is inside the new npm window until 2026-10-01.
- Security updates are not delayed: Dependabot cooldowns apply to version updates only.

## Constitutional impact

The delta ADDS a requirement to `openspec/specs/maintenance/spec.md`. It tightens CI's supply-chain
inputs; it changes no script, no vault content and no existing requirement. `overrides: none`.

```constitutional-impact
touches: openspec/specs/maintenance/spec.md
protects: [INV-2, INV-3, INV-6]
overrides: none
basis: ADD-only; pins CI inputs immutably and declares the update cooldown; no existing requirement modified
```

## Verification

- `tests/test_supply_chain_pins.py` **observed to fail first** on the unpinned tree: 25 tag refs, and
  `{'github-actions': None, 'pip': None, 'npm': None}` cooldowns. Green after.
- Mutation checks: dropping one `# v7.0.1` comment fails the version-comment test; reverting one pin to
  `@v7` fails the pin test. Both restored.
- The vacuity guard asserts the scan found ≥ 20 `uses:` lines; the parser test proves one ecosystem's
  cooldown cannot satisfy another's.
- CI on the PR itself exercises every pinned action.
