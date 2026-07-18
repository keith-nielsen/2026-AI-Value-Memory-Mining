<!-- SPDX-License-Identifier: Apache-2.0 -->
# Contributing to value-memory-mining

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

### Shipping a version (tag → release → mirror)

After a change is merged to `main`, the ship is **not complete** until a GitHub **Release object**
exists for the new version. A git tag and a GitHub Release are different objects — pushing a tag does
**not** create a Release, and the Releases page / profile badge track the newest *Release*, not the
newest tag. The ceremony is driven by the guarded state machine `tools/ship-release.py`:

```
1. tools/ship-release.py vX.Y.Z      # proves merge-ancestor + CHANGELOG entry, refuses stale
                                     # tags naming the true cause, cuts + verifies the local tag,
                                     # then EMITS the next single outward command and exits 2
2. Run exactly the emitted command (git push origin refs/tags/vX.Y.Z, later
   gh release create vX.Y.Z --verify-tag --latest …) through the normal gated channel
3. Re-run tools/ship-release.py vX.Y.Z — it verifies the mutation actually landed
   (per layer: remote-tag, release-object) before emitting the next step
4. Repeat until it prints the tag↔Release PARITY TALLY with its denominators and exits 0
5. Mirror any vault-template hook/guard change into the live vault (operator action),
   then prove it: tools/template-parity.py <VAULT_ROOT>
```

The driver deliberately **never executes the outward commands itself** — `git push` and
`gh release create` are ASK-gated by the INV-14 outbound guard, and the operator approves each
deliberately after reviewing the overview summary + `proposal.md`. Because release creation and
verification are steps the driver refuses to skip, a tag can never again accumulate without its
Release (the drift that stranded the Releases page at v0.1.13 while tags ran to v0.1.22 — and the
F10 record of seven false starts in one hand-driven ship is why the guards exist).

### Touching a constitutional element?

If your change modifies anything tagged `protects:` in the spec files, or touches
`openspec/constitution.md` itself, you must use the **Informed-Upheaval Protocol**
instead of the standard flow. Read `openspec/constitution.md` §3 carefully, then:

```
Use the template at: openspec/templates/constitution-override/proposal.md
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

## License

By contributing, you agree that your contributions are licensed under the
Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
