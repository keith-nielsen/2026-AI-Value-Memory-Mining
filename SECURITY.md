<!-- SPDX-License-Identifier: Apache-2.0 -->
# Security Policy

## Scope

This repository contains a **template and SDD specification** — it does not run
as a service and has no network-exposed attack surface of its own. Security
concerns fall into two categories:

1. **Template security** — vulnerabilities in the vault scripts, hooks, or
   configuration shipped in `vault-template/` that could affect adopters.
2. **Methodology security** — design flaws in the access-control model, agent
   containment rules, or invariants that weaken the security posture of a
   deployed vault.

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report privately by emailing the maintainer (see repository profile) or by using
GitHub's private vulnerability reporting if enabled for this repository.

Include:
- Which component is affected (`vault-template/`, `openspec/`, methodology design)
- The INV invariant(s) involved, if applicable
- Proof-of-concept or reproduction steps

## Relevant Invariants

The following invariants are directly security-relevant; a bypass of any of them
is a reportable vulnerability:

| INV | Description |
|-----|-------------|
| INV-4 | Bounded write scope — agent/LLM cannot write Treasury or Operations |
| INV-5 | Actor ≠ owner — no automated process writes `99-Operations/` |
| INV-7 | No secrets in vault — credentials must never appear in vault files |
| INV-11 | Name conformance — prevents path-traversal and shell injection via filenames |

## Known Deferred Security Work

The following hardening items are explicitly deferred (PRD §14.1) and are **not**
vulnerabilities in the current release:

- OS-level write-protection of `99-Operations/` (INV-5 is honored by design;
  enforcement via ACLs is deferred)
- osquery file-integrity monitoring and network egress enforcement
- Sandboxing of Hermes Agent workers (containment is via the commit-gate hook,
  not OS sandbox)
