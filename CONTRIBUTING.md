<!-- SPDX-License-Identifier: Apache-2.0 -->
# Contributing to memory-mining

## The method IS the process

This repository is governed by OpenSpec SDD. **Every change — bug fix, enhancement,
new capability — originates as an OpenSpec change proposal.** There are no drive-by
edits to `vault-template/` or `openspec/specs/`.

### Standard contribution flow

```
1. Fork and clone
2. /opsx:propose "what you want to change"
3. Fill out proposal + specs + design + tasks
4. /opsx:apply  (implement the tasks)
5. /opsx:archive (sync delta specs into main specs)
6. Open a PR — the PR template checklist will guide you
```

### Touching a constitutional element?

If your change modifies anything tagged `protects:` in the spec files, or touches
`openspec/constitution.md` itself, you must use the **Informed-Upheaval Protocol**
instead of the standard flow. Read `openspec/constitution.md` §3 carefully, then:

```
Use the template at: openspec/changes/templates/constitution-override/proposal.md
Change type must be: constitution-override
All four gates must be satisfied before the PR can merge.
```

CI will fail if a `protects:`-tagged file is modified without the ceremony.

### What makes a good contribution

- **Specs before code.** The proposal explains *why*; the spec captures *what changes*;
  the design explains *how*. Implementation without these is incomplete.
- **One change, one purpose.** Don't bundle unrelated capabilities.
- **Preserve invariants.** INV-1 through INV-13 are not negotiable via a normal change.
  If you believe an invariant is wrong, that is a constitutional override.
- **No vendored dependencies.** Third-party tools (Obsidian, n8n, Hermes, Ollama) are
  orchestrated, not embedded. If a component is embedded, verify its license first.
- **Apache hygiene.** New files get the SPDX header: `<!-- SPDX-License-Identifier: Apache-2.0 -->`.

### Reporting bugs

Use the **Bug Report** issue template. Include the INV ID of the invariant violated,
if applicable.

### Proposing a new capability

Use the **Change Proposal** issue template to discuss before opening a PR, especially
for larger changes.

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md).
All contributors are expected to uphold it.

## License

By contributing, you agree that your contributions are licensed under the
Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
