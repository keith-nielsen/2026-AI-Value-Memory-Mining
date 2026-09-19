---
type: meta-script
deploy_target: .claude/hooks/gh-invocation-guard.py
runtime: harness hook
class: script
created: 2026-08-25
updated: 2026-08-25
---
## Rationale

Claude Code `PreToolUse` guard — the **`gh` invocation-form allowlist** (ADR-0045). `gh api` with a
REST path and `gh auth status` are permitted; `gh api graphql` is excepted back into deny; every
other `gh` form is refused by default. Deterministic (INV-6): reads stdin only, spawns nothing,
touches no network. This note is its source of truth (INV-3) — `render` deploys the code block and
`reconcile` guards it like every other fleet member. `.claude/` is agent-write-denied in a live
vault, so rendering there is an operator action, matching the `outbound-publish-guard` precedent.

**Why GraphQL is prohibited: it is non-deterministic, and a production system cannot be built on
it.** The `gh pr` / `gh issue` / `gh run` family routes through GitHub's GraphQL endpoint, and this
estate has met its **silent no-op** failure four times: a mutation reports nothing actionable and
changes nothing, so a caller that trusts its exit status proceeds on a false belief. The record:

| Date | Instance |
|---|---|
| 2026-07-18 | `add-ship-ceremony-tools` — *"a GraphQL mutation can fail silently where REST succeeds"*; the mandatory post-mutation re-read exists because of this |
| 2026-07-19 | **F21** — `gh pr edit --body-file` exit 1 behind the Projects-classic deprecation, body **unchanged**; caught only because it was re-read |
| 2026-08-04 | **F21·3** — `gh pr edit --base` **silently no-opped**; `pr-flow.py` replaced it with `gh api -X PATCH` plus a re-read of the base |
| 2026-08-24 | `seed-auto-memory-store` — `gh pr edit` *"changed nothing, while reporting nothing actionable"* |

A channel that reports success without effect is unsuitable to task at any authentication state. The
cost is already paid and visible: `AGENTS.md` mandates a re-read after **every** `gh`/GraphQL
mutation — a permanent workaround for a channel that cannot be trusted to have acted. REST is the
recorded working route in every one of the four instances.

⚠ **This paragraph previously argued from `UNAUTHENTICATED`/401** — that GraphQL 401s because a
confined session's credential is unreadable. That ground was **measured false on 2026-08-26**: a
session launched with `$FRAMEWORK_ROOT` as its project directory has no `sandbox` block, reaches the
keyring, and `gh auth status` reports authenticated with `repo` and `workflow` scopes. The
credential state is a property of *which directory the session started in*, not of the platform, so
it could never have carried this rule. It was also a **regression against what this corpus already
knew**: `seed-auto-memory-store` had recorded that `gh pr *` is denied *"precisely for"* the silent
no-op. The determinism ground is session-independent and is the real one.

An enumerated deny list
cures the forms already known to have failed and permits every subcommand GitHub ships next — that
is enumeration drift, and curing it with a longer enumeration reproduces the disease. Inverting the
rule makes the unlisted case *refused* rather than *permitted*.

**Why this is a second hook rather than an extension of `outbound-publish-guard`.** That file is
load-bearing for INV-14, `inv6-offline-check` AST-analyses it specifically, and it rests on a stated
invariant that it *"may only ever DOWNGRADE a confirmation to an allowance"*. A new refusal class
sitting beside that invariant would make every future edit to `gh`-form ergonomics an edit to the
exfil path. Both hooks are pure `stdin`→`stdout` JSON contracts, so separation costs one note, one
render target and one test module.

### This guard emits `deny` or nothing — never `allow`

A permitted form produces **no output at all**. That is deliberate and load-bearing:

- an `allow` is a *decision*, and this guard has no business expressing one about `git push`,
  which is the outbound guard's subject matter. Deferring leaves that guard's behaviour
  byte-identical to its pre-change state;
- multi-hook precedence was **measured** 2026-08-25 (task G1.1): a `deny` from any hook wins over an
  `allow` or `ask` from any other, in either registration order. So a `deny` here is sufficient, and
  an `allow` here would buy nothing while risking the suppression of another guard's prompt.

### Both layers are kept, deliberately

| Layer | Coverage | Failure direction |
|---|---|---|
| this hook | general — any `gh` form | **fails OPEN** (a crashed hook exits non-zero and the harness defers) |
| `permissions.deny` | enumerated — five known offenders | **fails CLOSED** (harness-enforced, needs no process) |

A crashed interpreter, a malformed payload, or a fresh clone whose hooks are unrendered all resolve
to *permit* under this hook alone. Five lines of enumeration cover the general control's own outage.
**This redundancy is recorded so a later simplification does not remove it as duplication.**

### Limits — what this provably does NOT catch

A control whose limits are undocumented gets trusted past them. This is a **text matcher over the
command a Bash tool call carries**, and the threat model is the agent *forgetting*, not *evading*:

- **variable indirection** — `C=gh; $C pr list`
- **shell alias or function** — `alias g=gh; g pr list`
- **encoded execution** — `echo <base64> | base64 -d | sh`
- **subprocess invocation** — any program that calls `gh` internally. The harness hands this hook
  the command the agent *typed*, so `python3 <some-tool>` is what arrives, never the `gh …` the
  tool runs inside itself. **The agent typing a refused form is refused; a program calling it is
  not.** This is not a residual gap to be closed later: it is the boundary of what a matcher over
  a typed command can bind, and every ceremony tool that reads GitHub sits on the far side of it.
- **CI** — `.github/workflows/` runs `gh` on GitHub-hosted runners where no harness, no hook and no
  `permissions` block exists at all.

It also does not touch prose: the agent may still write, quote or propose a refused form. Execution
is governed; suggestion is not.

### Matching is by command-word position, not token presence

Each segment of a compound command is examined separately, leading environment assignments are
stripped, and the command word is compared by **basename** — so `/usr/bin/gh`, `GH_TOKEN=x gh` and
`cd /tmp && gh …` are all caught. A `gh` appearing anywhere other than the command-word position is
**data, not a command**, which is why `echo "run gh pr list"` is not refused. A guard that refused
prose about itself would be unusable.

## Implementation
```python
#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""PreToolUse hook — `gh` invocation-form allowlist (ADR-0045).

Emits a `deny` decision, or nothing at all. Never emits `allow`: see the note's Rationale.
Deterministic (INV-6) — reads stdin, spawns no subprocess, touches no network.

Fails OPEN by construction: any parse failure exits 0 with no output. That is why the enumerated
`permissions.deny` entries are retained alongside this hook rather than replaced by it.
"""
import json
import shlex
import sys

# The permitted set. Derived from a measured platform constraint, not from incident history:
# GitHub's GraphQL endpoint requires auth unconditionally, REST does not.
SEPARATORS = {"&&", "||", ";", "|", "&", "\n"}

REST_HINT = (
    "Use `gh api` with an explicit REST path instead — e.g. "
    "`gh api repos/{owner}/{repo}/pulls`. Permitted forms: `gh api <REST path>`, `gh auth status`."
)

# The sanctioned WRITE set. `gh api` is a wider permission than the subcommands it replaces --
# `gh api -X DELETE /repos/{owner}/{repo}` is permitted by form alone -- so GET is unconstrained
# and every write method reaches only these endpoints.
#
# IMPORTED, NOT AUTHORED HERE. The source of truth is the ```gh-write-endpoints block in
# docs/version-control-legal-moves.md §2b; tests/test_write_endpoint_set_parity.py fails if this
# copy drifts from it. The copy exists because this guard is stdlib-only, offline and deterministic
# (INV-6) and renders into roots that have no docs/ directory -- it cannot read that file at runtime.
# Edit the doc block, then this constant, never one alone.
#
# {slug} spans two path segments (owner/repo); {n} and {id} are numeric.
SANCTIONED_WRITES = {
    ("POST", "/repos/{slug}/pulls"),
    ("PATCH", "/repos/{slug}/pulls/{n}"),
    ("PUT", "/repos/{slug}/pulls/{n}/merge"),
    ("POST", "/repos/{slug}/releases"),
    ("DELETE", "/repos/{slug}/releases/{id}"),
    ("POST", "/repos/{slug}/labels"),
    ("POST", "/repos/{slug}/issues"),
}


def segments(command):
    """Split a command line into segments on shell separators, quote-aware.

    `shlex` with punctuation_chars emits `&&`, `||`, `;` and `|` as their own tokens while leaving
    quoted text intact — so `echo "a && b"` is one segment, and `cd /tmp && gh pr list` is two.
    """
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    out, current = [], []
    for tok in lexer:
        if tok in SEPARATORS:
            out.append(current)
            current = []
        else:
            current.append(tok)
    out.append(current)
    return [s for s in out if s]


def is_env_assignment(token):
    """`VAR=value` in command-word position is an assignment, not the command."""
    if "=" not in token:
        return False
    name = token.split("=", 1)[0]
    return bool(name) and (name[0].isalpha() or name[0] == "_") and \
        all(c.isalnum() or c == "_" for c in name)


def verdict(segment):
    """-> reason string to deny with, or None to stand aside."""
    args = list(segment)
    while args and is_env_assignment(args[0]):
        args.pop(0)
    if not args:
        return None

    # Compare by basename so an absolute path cannot walk past the matcher.
    if args[0].rsplit("/", 1)[-1] != "gh":
        return None

    rest = args[1:]
    positional = [a for a in rest if not a.startswith("-")]
    sub = positional[0] if positional else ""

    if sub == "api":
        # `gh api` is permitted EXCEPT the one form this estate has measured unsuitable: graphql.
        # The reason states only what is invariant. A hook is deterministic and offline (INV-6), so
        # it can never measure the session's credential -- any message asserting one would be a
        # claim the control cannot check, and was wrong in the field on 2026-08-26.
        if len(positional) > 1 and positional[1] == "graphql":
            return (
                "`gh api graphql` is refused: GitHub's GraphQL endpoint has failed "
                "non-deterministically in this estate four times, each a SILENT NO-OP -- the "
                "mutation reported nothing actionable and changed nothing (F21, F21-3). A channel "
                "that reports success without effect is unsuitable for production use. " + REST_HINT
            )
        return None

    if sub == "auth" and len(positional) > 1 and positional[1] == "status":
        return None

    named = f"`gh {sub}`" if sub else "this `gh` form"
    return (
        f"{named} is refused: the `gh` invocation-form allowlist permits only `gh api` with a REST "
        f"path and `gh auth status`; every other form is refused by default rather than permitted "
        f"by omission (ADR-0045). " + REST_HINT
    )


def main():
    try:
        payload = json.load(sys.stdin)
        command = payload["tool_input"]["command"]
        if not isinstance(command, str):
            raise TypeError
        parts = segments(command)
    except Exception:
        return  # fail open — silence, exit 0

    for segment in parts:
        reason = verdict(segment)
        if reason:
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }))
            return


main()
```
