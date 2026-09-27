<!-- SPDX-License-Identifier: Apache-2.0 -->
# Spec delta: maintenance

## ADDED Requirements

### Requirement: The Pre-Flight Refuses An Interpreter That Cannot Run The Suite

Every job the pre-flight runs executes under one interpreter — the one that launched it. An
interpreter lacking the test suite's own declared requirements makes those jobs fail for a reason
that lies in the environment, not the change, and the pre-flight then scores the environment as a
defect: a non-result reported as a result, which the pre-flight's own requirement forbids.

Before running any job, the pre-flight SHALL verify that the interpreter its jobs run under has every
distribution the suite's requirements file declares. It SHALL verify this the way the jobs are
launched — as a child process of that interpreter — and SHALL NOT infer it from its own process,
whose view of installed packages can differ from its children's.

Where a declared distribution is missing, the pre-flight SHALL refuse: it SHALL name the interpreter
and each missing distribution, SHALL run no job, SHALL give no verdict — neither clear nor findings —
and SHALL exit with a status distinct from both. A refusal SHALL NOT be counted as a finding.

Where no requirements file exists, there is nothing declared to verify, and the pre-flight SHALL
proceed and say so.

#### Scenario: The interpreter lacks a declared test requirement

- **WHEN** the pre-flight is launched by an interpreter that lacks a distribution the suite's
  requirements file declares
- **THEN** it names that interpreter and the missing distribution
- **THEN** it runs no job and reports neither a clear result nor any finding
- **THEN** it exits with a status distinct from both a clear result and findings

#### Scenario: The interpreter has every declared requirement

- **WHEN** the pre-flight is launched by an interpreter that has every declared distribution
- **THEN** it proceeds to run the jobs and gives a verdict as before

#### Scenario: The pre-flight's own process sees fewer packages than its jobs

- **WHEN** the pre-flight process is started with a flag its child processes do not inherit
- **THEN** the requirement check reflects what the jobs will see, not what the parent process sees
