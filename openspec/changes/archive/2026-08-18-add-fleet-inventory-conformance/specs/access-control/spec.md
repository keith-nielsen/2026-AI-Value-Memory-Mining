<!-- SPDX-License-Identifier: Apache-2.0 -->

## ADDED Requirements

### Requirement: Harness Command Exclusions Name Artifacts That Exist

Every command path declared in a harness settings file — the repository's own `.claude/settings.json`
and the one shipped in `vault-template/` — SHALL resolve to an artifact declared as a `deploy_target`
by a current script note. This SHALL be mechanically verified.

An exclusion entry is matched as an **exact string**. When the artifact it names moves or is retired,
the entry does not error: it silently ceases to match, and the resulting refusal is indistinguishable
from a genuine denial. The surrounding tooling cannot observe this — the fleet's tests invoke scripts
as subprocesses and never traverse the harness, so an exclusion may be broken while every test
reports green.

**The verification SHALL be demonstrated capable of failing.** A check written against a
currently-valid configuration passes on the day it is written and proves nothing; its red state SHALL
be manufactured and recorded at least once. A check never observed refusing is an assumption.

**Stated limit.** This verification establishes that a declared path **resolves**. It cannot
establish that the exclusion **matches** at the harness layer, because no automated test traverses
the harness. Only a real agent invocation can confirm that, and it is therefore an operator step, not
a gate. This limit is recorded here rather than left to be discovered, because a check that appears
to cover the harness and does not is worse than no check.

#### Scenario: An exclusion naming a moved artifact is caught
- **WHEN** a settings file declares a command path that no current script note declares as a `deploy_target`
- **THEN** the settings resolution check fails, naming the file and the unresolved path

#### Scenario: The check is proven capable of refusing
- **WHEN** a settings file is temporarily pointed at a nonexistent artifact
- **THEN** the settings resolution check fails, and the recorded failure is retained as evidence
