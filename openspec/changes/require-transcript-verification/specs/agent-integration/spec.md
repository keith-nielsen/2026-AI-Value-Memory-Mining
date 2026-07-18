<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: Verification Deliverables Are Transcripts

An *enumerate* or *verify* step in a governed procedure SHALL be satisfied only by a pasted,
re-runnable command transcript: the exact command(s) plus their full, untruncated output.
This applies wherever such a step appears — the Informed-Upheaval gates, an ordinary change's
tasks, a runbook checklist. A list or verdict composed from reasoning SHALL NOT satisfy the
step.

Rationale (the failure record this encodes): enumeration performed by reasoning is bounded by
what the agent thought of, not by the corpus, and has shipped misses three times (F8, F9, F17 in
the live vault's determinism-failure-modes record); a check whose failure case is not observable
has produced false "all green" verdicts (F20, three instances in one session). A transcript
converts "did the agent think of everything?" (unfalsifiable) into "does the transcript match
the corpus?" (re-runnable, diffable).

Constraints on the transcript:

- The output SHALL NOT be truncated (`head`/`tail`/sampling): narrowing the output is the same
  defect as narrowing the scope.
- Every hit in an enumeration transcript SHALL be dispositioned (edited here / not edited,
  with reason) so the reviewer can diff hits against actions.
- Verification evidence SHALL be a form that shows its own denominator or failure case — a
  tally, a diff, an exit status. A literal verdict string printed by the shell (`echo "ok"`,
  `... || echo "clean"`) SHALL NOT count as evidence: the shell knows only an exit code, not
  the answer to the question asked.

#### Scenario: A blast-radius enumeration is satisfied by a transcript

- **WHEN** a `constitution-override` proposal reaches Gate 1
- **THEN** its blast-radius section contains the search command(s) and their full output
- **THEN** the Gate-4 reviewer re-runs the command(s) and diffs; a clean diff confirms the
  enumeration, a dirty diff rejects it

#### Scenario: A composed list without a transcript is rejected at review

- **WHEN** a proposal's enumeration or verification step is a prose list with no command
  transcript
- **THEN** the review rejects the gate as unsatisfied, regardless of the list's apparent quality

#### Scenario: A truncated enumeration is invalid

- **WHEN** an enumeration transcript pipes through `head -N` or otherwise samples its output
- **THEN** the step is unsatisfied — the transcript must carry the full output

#### Scenario: A shell-printed verdict is not verification evidence

- **WHEN** a verification step's evidence is a success string emitted by `&& echo` / `|| echo`
- **THEN** the step is unsatisfied; the deliverable is the underlying evidence (tally, diff,
  exit status) read by the reviewer
