<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0024: Empty `index_links` defaults to a pending-catalog holding index

- **Status:** Proposed (flips to Accepted at Gate 4)
- **Date:** 2026-07-11
- **Change:** `bank-execute-pending-catalog` (`constitution-override`; touches `maintenance` spec,
  `protects: [INV-2, INV-3, INV-6]`)
- **Supersedes/relates:** extends ADR for `bank-execute-pre-flight` (the B4 pre-flight battery)

## Context

The refine executor is the sole automated writer of `40-Treasury/`. Its pre-flight validates that a
proposal's `index_links` is a *list*, but not that the list is non-empty. A `"index_links": []`
proposal therefore banks a knowledge note wired into **no** Catalog index — an orphan, unreachable from
any pillar front door, contradicting INV-12 (discovery via Catalog links, never folders). The gap is
also inconsistent with the executor's own contract, which hard-rejects a proposal naming a *broken*
index link. Surfaced by the Crucible prove-out dig (Qwen dry-run, finding #10) and verified against the
live vault: the three real Treasury deposits to date all carried non-empty `index_links`, so no real
workflow relies on the empty case.

## Options

1. **Hard-reject empty `index_links`.** Simple, consistent with the other pre-flight rejects.
   *Cost:* blocks banking genuine refined value over a curation detail; forbids any "bank now, catalog
   later" flow.
2. **Warn-only.** Bank the orphan, print a warning; rely on `treasury-orphan` to catch it later.
   *Cost:* the only soft check in an otherwise all-or-nothing pre-flight; permits exactly the silent
   orphan the gate exists to prevent.
3. **Default to a holding index (chosen).** Bank the note, but link it into a dedicated
   `pending-catalog-index.md` when `index_links` is empty. The note is always reachable; the holding
   index is a *visible* "awaiting-catalog" queue. This is the industry-standard **inbox pattern**
   (GTD capture→inbox→clarify; Zettelkasten fleeting→permanent) applied at the refined layer.

## Decision

Adopt option 3. The executor normalizes an **explicit empty list** to
`["40-Treasury/Catalog/pending-catalog-index.md"]` before the containment and link-target checks; a
*missing* or *non-list* `index_links` remains a Schema rejection. The holding index ships in the
template and is created per-deployment by the operator (Treasury is autonomy-banned). Until it exists,
an empty-`index_links` proposal safely rejects via the existing missing-target rule — fail-safe, never
a silent orphan.

## Consequences

- **Positive:** INV-12 reachability is guaranteed for every banked note; progress is never blocked on a
  missing pillar link; outstanding curation is a first-class browsable queue, not a background scan;
  the pre-flight is now internally consistent (empty ≈ named-but-defaulted, both reachable).
- **Determinism/atomicity unchanged (INV-2/3/6):** still one atomic scoped commit per bank, still
  deterministic, no network/LLM. The default is a pure in-memory list substitution.
- **Sacrifice:** banking a note with **zero** Catalog links in a single step is no longer possible —
  every banked note is linked somewhere. Forks inherit a `pending-catalog-index.md` they must keep.
- **Risk:** the holding queue can become an un-emptied junk drawer. Mitigation is visibility — a
  count via `treasury-orphan` / daily close — and even unmanaged it is strictly better than a silent
  orphan.
