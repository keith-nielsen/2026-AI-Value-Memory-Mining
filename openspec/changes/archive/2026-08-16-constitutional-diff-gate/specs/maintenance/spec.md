<!-- SPDX-License-Identifier: Apache-2.0 -->

## ADDED Requirements

### Requirement: A Diff Touching A Protected Element Declares Its Constitutional Impact

A change whose diff modifies a specification file carrying a `protects:` frontmatter tag SHALL carry
an explicit declaration of that change's constitutional impact, and continuous integration SHALL
refuse a change that supplies none.

The subject set SHALL be determined by reading **YAML frontmatter**, and SHALL NOT be determined by
matching the string `protects:` anywhere in a file's contents. Documentation, changelogs, workflow
definitions, architecture decision records and the constitution itself all quote the tag in prose; a
substring match refuses them all, including the file that implements the gate and the constitution the
gate exists to protect.

The declaration SHALL enumerate the protected identifiers that the touched files carry, and SHALL
state which of those identifiers, if any, the change **overrides**. Where the declaration states that
no identifier is overridden, the gate SHALL pass.

The gate SHALL NOT evaluate whether a declaration is correct. Determining whether a change overrides a
principle is the human judgement the Informed-Upheaval Protocol reserves, and a gate that guessed at it
would refuse legitimate work while lending false authority to its own verdict. The gate establishes
that the question was answered in writing and that the answer is in version control; it establishes
nothing further, and its reporting SHALL NOT imply otherwise.

Where the declaration names one or more overridden identifiers, the gate SHALL require a
`constitution-override` change directory in the same diff, carrying the four gate sections the
protocol mandates, and SHALL refuse the change where it is absent.

The gate SHALL NOT refuse a change that carries a complete `constitution-override`. A guard that
refuses the ceremony it demands teaches its reader to bypass it, and would discredit the protocol it
serves.

A change that synchronises a delta into a specification file as part of archiving SHALL pass where the
declaration is present in the change directory being archived, whether that directory is read at its
live path or at its archived path. Archiving moves a directory and applies its delta, so it touches
protected specifications by construction and is a routine ceremony step rather than a constitutional act.

A refusal SHALL name the protected files the diff touched, the identifiers those files carry, and the
declaration the change is missing. A guard that reports only a verdict obliges its reader to derive the
remedy, which is the condition under which readers learn to route around guards.

#### Scenario: A protected specification is modified with no declaration
- **WHEN** a diff modifies a specification file carrying a `protects:` frontmatter tag
- **AND** the change supplies no constitutional-impact declaration
- **THEN** the gate refuses the change
- **THEN** the refusal names the touched file, the identifiers it carries, and the declaration required

#### Scenario: A declaration states that nothing is overridden
- **WHEN** a diff modifies a protected specification
- **AND** the declaration names no overridden identifier
- **THEN** the gate passes
- **THEN** the gate does not evaluate whether the declaration is accurate

#### Scenario: A declaration names an overridden identifier
- **WHEN** a declaration names one or more overridden identifiers
- **AND** the diff carries no `constitution-override` change directory
- **THEN** the gate refuses the change
- **THEN** the refusal names the identifiers claimed as overridden

#### Scenario: A constitution-override change is evaluated by the gate
- **WHEN** a diff carries a `constitution-override` change directory with its four gate sections present
- **THEN** the gate passes
- **THEN** the gate does not refuse the change on account of the protected files that change touches

#### Scenario: A file quotes the protects tag in prose
- **WHEN** a diff modifies a file that contains the string `protects:` in its body but carries no
  `protects:` frontmatter tag
- **THEN** the gate does not fire
- **THEN** the constitution, the changelog, the contributing guide and the workflow definitions are
  outside the subject set on this basis

#### Scenario: An archive synchronises a delta into a protected specification
- **WHEN** a diff moves a change directory into the archive and applies its delta into a protected
  specification
- **AND** the archived change directory carries a constitutional-impact declaration
- **THEN** the gate passes
- **THEN** the declaration is located whether the change directory is read at its live or archived path

### Requirement: A Constitutional Declaration Is Read From The Tree, Not The Pull-Request Body

The constitutional-impact declaration SHALL be read from a file in the change's own diff, and SHALL
NOT be read from pull-request metadata.

A pull-request body may be edited after its checks have reported, and editing it does not re-evaluate
them. A declaration held there can therefore be made to say something other than what was verified,
while the verification remains green. For a claim about constitutional impact this is disqualifying:
the record and the check must be the same object, and that object must be versioned.

The declaration SHALL be discoverable without network access and without a pull request in existence,
so that the gate can be evaluated locally before a change is pushed.

#### Scenario: The declaration is present only in the pull-request body
- **WHEN** a change places its constitutional-impact declaration in the pull-request body alone
- **THEN** the gate refuses the change
- **THEN** the refusal states that the declaration must be committed to the tree

#### Scenario: The gate is evaluated locally before any pull request exists
- **WHEN** the gate runs against a local branch with no pull request open
- **THEN** it reaches the same verdict it would reach in continuous integration
- **THEN** it requires no network access to do so

#### Scenario: A declaration is amended after review
- **WHEN** a committed declaration is amended
- **THEN** the amendment appears in the diff under review
- **THEN** continuous integration re-evaluates the gate against the amended declaration
