## ADDED Requirements

### Requirement: A Formatting Change Is Proven To Preserve Content

A change that reformats markdown across the corpus SHALL be accompanied by evidence that prose was
preserved, produced by an instrument rather than by review. The repo SHALL therefore provide a
deterministic, offline, detection-only checker that compares two revisions of every changed markdown
file and classifies each into exactly one of three states: **identical** (same tokens, same order),
**reordered** (same tokens, new order), or **changed** (tokens added or removed).

Comparison SHALL be insensitive to formatting a linter may legitimately alter — line reflow,
blank-line insertion, table realignment, fence language labels, and list-bullet style — by collapsing
every whitespace run and excluding structural tokens. It SHALL be sensitive to any word, number,
punctuation-bearing token or significant whitespace **inside a code span** that is added or removed.

The checker SHALL be **detection-only**: it reports and exits non-zero, and never edits a file. A
path whose prose change has been reviewed and accepted SHALL be declarable, so that acceptance is
recorded explicitly rather than achieved by weakening the check.

The checker SHALL carry a **selftest** that proves both directions — that formatting-only input is
reported identical, and that a known real defect is reported changed — because an instrument that
cannot fail proves nothing about the corpus it blesses.

The checker SHALL state its blind spot in its own documentation, and that blind spot SHALL be pinned
by a test, so it cannot widen without a test failing.

⚠ **Scope.** This requirement governs evidence that content survived a reformat. It is not a
renderer, makes no claim that two revisions LOOK identical, and does not judge whether a reported
difference is acceptable — that judgement is the reviewer's.

#### Scenario: A formatting-only sweep is proven to preserve content

- **WHEN** a markdown file is reflowed, has blank lines inserted, has its tables realigned, has fence
  language labels added, and has its list bullets restyled
- **THEN** the checker reports `identical` for that file
- **THEN** it exits `0`, because nothing in the prose changed

#### Scenario: An autofix strips a significant character

- **WHEN** a code span whose trailing space is the content — such as a validator test input — has that
  space removed by a mechanical fixer
- **THEN** the checker reports the file as `changed` and names the tokens removed and added
- **THEN** it exits non-zero, so the sweep cannot be merged as formatting-only

#### Scenario: Content is moved rather than lost

- **WHEN** entries are relocated between duplicate sections without any word being added or removed
- **THEN** the checker reports `reordered`, not `changed`
- **THEN** the distinction is visible to the reviewer, so a consolidation is not mistaken for a loss

#### Scenario: The instrument proves itself before it is trusted

- **WHEN** the checker is run with its selftest flag
- **THEN** it verifies that formatting-only input reports identical AND that a known defect reports
  changed
- **THEN** it exits non-zero if either direction fails

#### Scenario: An unreadable revision range is refused, not guessed

- **WHEN** the checker is given a base or head that does not resolve
- **THEN** it exits `2` with a `MALFORMED:` line and no traceback
