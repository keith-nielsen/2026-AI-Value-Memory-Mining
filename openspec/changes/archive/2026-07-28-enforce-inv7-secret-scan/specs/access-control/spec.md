<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: Secrets Prohibition Is Enforced at the Boundary

INV-7 SHALL be enforced mechanically at the commit boundary, not asserted as a prohibition and
verified by inspecting configuration.

A credential-format scanner (`~/bin/vault_secrets.py`, rendered from
`99-Operations/scripts/secret-scan-script.md`) SHALL classify matches into two tiers:

- **HIGH** — anchored vendor token formats whose false-positive rate is effectively zero.
- **ADVISORY** — contextual patterns (e.g. `password = "…"`) with a real false-positive rate over
  a corpus that legitimately discusses credentials.

The commit gate SHALL consult **only the HIGH tier**. Advisory matches SHALL be reportable by the
standalone tool and SHALL NOT block a commit. A gate that fires on prose about credentials
destroys its own signal value and impedes the audit most likely to find its defects.

The scan SHALL cover staged **content** across `git diff --cached --diff-filter=ACM` — every file
type, added and modified alike — and SHALL NOT grandfather existing files. This is deliberately
wider than the INV-11 half of the same gate, which is scoped to `AR`: a pre-existing non-conforming
*name* is cosmetic debt, a pre-existing *credential* is an active compromise.

Reported matches SHALL be redacted to a short prefix and a length. A scanner that emits the
secret it found violates INV-7 in the act of enforcing it.

The scanner SHALL run a selftest before every scan, proving its patterns fire and that the two
tiers are disjoint, and SHALL refuse to report a clean result if that selftest fails. A detector
that cannot be shown to detect anything reports "clean" for a clean corpus and for a broken
pattern set alike.

CI SHALL scan the repository's full object database — including **unreachable** objects from
discarded commits and dropped rebases — because a credential committed and later "removed"
survives there and is invisible to `git rev-list`.

**Honest bound, stated in the spec so it cannot be lost:** this mechanism detects *known formats*.
It does not detect a shapeless password, a secret split across lines, or an encoded one. A clean
scan SHALL NOT be cited as proof that no secret exists; it is a boundary gate, and credential
custody discipline is the other half of INV-7.

#### Scenario: A staged credential blocks the commit

- **WHEN** staged content contains a string matching a HIGH-tier credential format
- **THEN** the commit gate blocks the commit and names the file, line, and pattern
- **AND** the reported match is redacted — the full secret does not appear in the output

#### Scenario: Prose about credentials does not block the commit

- **WHEN** staged content merely discusses tokens, or contains an ADVISORY-tier pattern such as `password = "…"`
- **THEN** the commit proceeds — only the HIGH tier gates

#### Scenario: A credential is never grandfathered

- **WHEN** a file that already existed is modified to contain a HIGH-tier credential format
- **THEN** the commit is blocked, notwithstanding that the INV-11 half of the same gate would have
  grandfathered a pre-existing name

#### Scenario: The scanner refuses to report clean on a broken instrument

- **WHEN** the scanner's selftest fails to make its patterns fire, or the tiers are not disjoint
- **THEN** it exits non-zero with a selftest failure and reports no verdict about the content

#### Scenario: A secret in a discarded commit is still found

- **WHEN** a credential was committed and the commit was later discarded, leaving the blob unreachable
- **THEN** the historical scan reports it, identifying the object as an unreachable blob
