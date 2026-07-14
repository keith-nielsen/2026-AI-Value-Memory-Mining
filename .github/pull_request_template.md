## Summary

<!-- 1-3 bullets describing what this PR changes and why -->

## Declared scope

<!-- Machine-checked by the scope-review CI job. List every path this PR is
     authorized to touch: root-relative, one per line, directories end with "/",
     no globs (they never match). Ceremony changes: copy the Gate-1 blast radius.
     Lines starting with "#" are comments. -->

```scope
openspec/changes/<change-id>/
CHANGELOG.md
```

## Change type

- [ ] Bug fix
- [ ] Spec / documentation update
- [ ] New capability (non-constitutional)
- [ ] Constitutional change (requires Informed-Upheaval Protocol — see `openspec/constitution.md`)

## Checklist

- [ ] CI passes (openspec validate, constitution-lint, vocabulary-lint, spec-lint, naming-validator)
- [ ] Declared-scope block present and matches the diff (ceremony changes: mirrors the Gate-1 blast radius)
- [ ] If touching a spec: `protects:` frontmatter is present and accurate
- [ ] If changing a constitutional element: Informed-Upheaval Protocol completed with human sign-off in `openspec/changes/`
- [ ] If changing `vault-template/99-Operations/scripts/`: code block updated in the literate note, `render` re-run, `reconcile` shows zero drift
- [ ] SPDX license header present on new source files (`SPDX-License-Identifier: Apache-2.0`)
- [ ] `CHANGELOG.md` updated under `[Unreleased]`

## Test plan

<!-- How did you verify this change? -->

## Related issues

<!-- Closes #... -->
