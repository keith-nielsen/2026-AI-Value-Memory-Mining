---
title: "Using This Template"
---

# Using This Template

This repo is a forkable, production-ready implementation of the Value Mining personal
knowledge system. Fork it once; configure your pillars; run the bootstrap; start
mining.

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| [Obsidian](https://obsidian.md) | Local-first Markdown editor; free for personal use |
| Python 3.12+ | For all operational scripts |
| Git | Version control; the vault is a repository |
| `python-frontmatter` | Installed into a vault-local venv (see Step 3) — modern distros block `pip install` into the system Python under PEP 668 |

**Declared floors** (spec: `maintenance` → "Platform and Dependency Floors"): Python ≥ 3.12
(CI tests 3.12 + 3.13); Linux/POSIX only — bash hooks, executable bits, and path semantics are
assumed, and Windows is an explicit non-goal; `python-frontmatter` is the fleet's *sole*
third-party dependency, and the hook-critical paths (`vault_naming.py --check`, the git hooks,
`vault_lib` root/config helpers) stay stdlib-only so they run on the system Python without the
venv.

Optional for Phase 3 (agent operations, deferred):
- [Hermes Agent v0.15.2](https://github.com/Nous-Research/hermes) — Kanban worker runtime
- [n8n](https://n8n.io) — Orchestration / egress-control layer
- [Ollama](https://ollama.ai) — Local model inference

---

## Fork and Clone

```bash
# Fork on GitHub, then:
git clone https://github.com/<your-username>/2026-AI-Value-Memory-Mining.git my-vault
cd my-vault
```

Or use the GitHub template button if this repo is marked as a template.

---

## Step 1: Copy the Vault Template

The `vault-template/` directory is your starting vault. Copy it to wherever you keep
your Obsidian vaults:

```bash
cp -r vault-template/ ~/Documents/my-vault
cd ~/Documents/my-vault
git init
git config core.hooksPath 99-Operations/hooks
git add -A
git commit -m "init: fork from value-memory-mining template"
```

---

## Step 2: Configure Your Pillars

Config is split into **public framework defaults** (`99-Operations/config.defaults.env`, tracked) and
your **private instance** (`99-Operations/config.env`, gitignored). Create your instance from the
example (it sources the defaults, then your overrides), then edit it:

```bash
cp 99-Operations/config.env.example 99-Operations/config.env
# in 99-Operations/config.env — replace with your own top-level life/knowledge domains
export PILLARS="mental health financial social technology calling"
```

**Pin `PILLARS` even if you keep the default set.** Left unpinned you inherit the framework's
*example* default, so a future update to the public `config.defaults.env` would silently re-pillar
your vault.

**Naming rule (ADR-0029): each pillar is ONE lowercase kebab slug; whitespace separates pillars.**

| You write | You get |
|---|---|
| `PILLARS="mental health financial"` | **3** pillars — `mental`, `health`, `financial` |
| `PILLARS="mental-health financial"` | **2** pillars — `mental-health`, `financial` |

A multi-word pillar is one hyphenated token. Whitespace *always* separates, so there is no way to put
a space inside a pillar name — deliberately: each pillar is interpolated straight into its Catalog
index filename (`<pillar>-domain-index.md`), which may not contain spaces (INV-11). The linter rejects
any token that is not a valid kebab slug (`Mental_Health`, `CON`, `-lead`).

Want a prettier display name? Alias it at the link, not in the vocabulary:

```markdown
[[mental-health-domain-index|Mental Health]]
```

Pillar design principles:
- **Distinct**: minimal overlap between pillars
- **Top-level**: no pillar should be a sub-category of another
- **Durable**: stable for years, not months
- **Kebab**: `mental-health` — never `mental health` (that is two pillars) or `Mental_Health` (rejected)

Then update `40-Treasury/Catalog/` to match. Either rename the example index files or
create new ones from `97-Molds/index-mold-blank.md`. The Home index (`home-master-index.md`) should link to
each of your pillar indexes.

---

## Step 3: Bootstrap Scripts

Create a vault-local virtual environment for the one Python dependency, then deploy
the operational scripts to the host. The venv keeps you off the system Python (which
modern distros lock down under PEP 668); `config.env` already adds `.venv/bin` to your
PATH, so sourcing it activates the right interpreter.

```bash
cd ~/Documents/my-vault

# 1. vault-local venv with the one dependency
python3 -m venv .venv
.venv/bin/pip install -r 99-Operations/requirements.txt

# 2. source config — sets VAULT_ROOT + vocab and puts .venv/bin on PATH
#    (make sure VAULT_ROOT in 99-Operations/config.env is this vault's absolute path)
. 99-Operations/config.env

# 3. bootstrap render from source (one-time; a meta-script note is Markdown,
#    so extract its code block rather than running the .md)
python3 - << 'EOF'
import re, pathlib, frontmatter, os
note = pathlib.Path("99-Operations/scripts/render-reconcile-script.md")
m = re.search(r"^```python\n(.*?)^```", frontmatter.load(note).content, re.S | re.M)
target = pathlib.Path(os.path.expanduser("~/bin/vault-render.py"))
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(m.group(1)); target.chmod(0o755)
print(f"bootstrapped -> {target}")
EOF

# 4. deploy all scripts, emit naming-rules.json, verify zero drift
python3 ~/bin/vault-render.py render
python3 ~/bin/vault_naming.py
python3 ~/bin/vault-render.py reconcile
```

---

## Step 4: Activate the Commit Gate

The pre-commit hook (INV-11) blocks commits with naming-violating filenames. It was
activated by `git config core.hooksPath 99-Operations/hooks` in Step 1. Verify:

```bash
git config core.hooksPath
# should print: 99-Operations/hooks
```

The hook fires on every commit — by human, script, or agent. It imports
`vault_naming.py` and is itself deployed by `render` (which marks it executable).

---

## Step 4b: Push Guard — Private by Default (INV-14)

Your vault is **private by default**. The `pre-push` hook (`push-guard-script`, deployed by `render`
alongside the commit gate) **refuses every `git push`** unless the target remote is listed in
`PUSH_ALLOWLIST` (`99-Operations/config.env`). With the allowlist empty (the default), the vault cannot
publish anywhere — a personal vault holds private, irreversible-if-leaked material.

To enable a **deliberate, PRIVATE** off-machine backup (never a public remote):

```bash
# 1) confirm the destination repo is PRIVATE and intended
# 2) add its URL (or a unique substring) to PUSH_ALLOWLIST in 99-Operations/config.env:
export PUSH_ALLOWLIST="github.com/you/my-vault-private"
# 3) re-source config.env, then push
```

For a deliberate **public FRAMEWORK mirror** (framework machinery only — never personal content), use
`PUBLIC_REMOTE_ALLOWLIST` instead: a remote listed there may receive **only** the paths in
`99-Operations/schemas/publish-manifest.json` (a default-deny allowlist); the guard refuses any private
path in the push, path-by-path (INV-14, ADR-0020). Both allowlists are empty by default.

Removing the guard entirely changes a **Tier-0 invariant (INV-14)** and requires the
constitution-override ceremony. If you use Claude Code, the bundled `.claude/` `PreToolUse` guard
additionally blocks the *agent* from pushing the vault outward and warns loudly before any public
publish (`gh repo create`, `npm publish`, `gh release`, …).

---

## Step 4c: Agent Write-Scope Sandbox (burn-in → strict)

The template's `.claude/settings.json` ships with the **agent write-scope enforcement** on
(`os-enforced-agent-write-scope`, ADR-0022): an OS sandbox denies agent shell writes — including any
child process or interpreter — to `40-Treasury/ 99-Operations/ .claude/ 96-Runbooks/ 97-Molds/
10-Logbook/`, and permission deny rules block the structured file tools on the same scope plus the
script-owned Logbook artifacts. Rendered vault scripts stay drivable via their **bare exact
invocation** (they are sandbox-excluded); system cron jobs are unaffected (cron is not the agent).

Sandbox dependencies (Linux/WSL2): `sudo apt-get install bubblewrap socat`. On Ubuntu 24.04+, if
`sysctl kernel.apparmor_restrict_unprivileged_userns` returns `1`, add the AppArmor `bwrap` profile
from the Claude Code sandboxing docs. macOS needs nothing (Seatbelt). Verify with `/sandbox` inside
Claude Code. Without the dependencies, Claude Code warns and runs unsandboxed — install them.

Adoption is **two-stage by design**:

1. **Burn-in (as shipped):** the sandbox escape hatch stays on — a command that fails under the
   sandbox falls back to the regular permission prompt. Treat every fallback as a signal: add the
   path to `sandbox.filesystem.allowWrite` or the command to `excludedCommands` deliberately.
2. **Strict (later, once burn-in is clean):** add `"failIfUnavailable": true` and
   `"allowUnsandboxedCommands": false` to the `sandbox` block. **Order matters:** never set
   `failIfUnavailable` before the dependencies verify green, or Claude Code will refuse to start.

---

## Step 5: There Are No Crons

**The vault installs no schedules and runs nothing on a tick.** It is a *self-priming pump, not a
driven one* (ADR-0028): every script resolves the vault root itself and runs bare, on demand, from
any directory, with no pre-sourced environment — invoked by an actor who decided to invoke it.

This is deliberate. An earlier version of this template declared `cron` schedules in script
frontmatter and documented crontab lines here. Nothing ever read those declarations: `render`
deploys code and marks it executable, it does not install schedules. The result was a cadence that
existed only on paper — and the artifacts built to assume it (a board, a carry-over list, and the
daily note itself) went unread and stale. A cadence a framework cannot install is a decoration, not a configuration.

Run what you need, when you need it:

```bash
python3 ~/bin/vault-refine-detect.py   # when you are about to refine
python3 ~/bin/vault-render.py reconcile  # when a script note changed
```

If you want a cadence, own it deliberately — in your own crontab, your harness, or your habit. The
framework will not assume one on your behalf.

Make sure `VAULT_ROOT` inside `config.env` is set to the absolute path of your vault
(Step 2). Sourcing `config.env` then provides everything each script needs.

---

## Step 6: Open in Obsidian

Open the vault folder in Obsidian. You'll find:

- `00-Docs/README.md` — orientation and getting-started guide (deletable after setup)
- `40-Treasury/Catalog/home-master-index.md` — master index linking to your pillar indexes
- `97-Molds/` — note templates (effort, knowledge, index)
- `99-Operations/` — all scripts and config (human-write-only)

For the recommended plugins, settings (incl. the default-new-note-location that keeps
your inbox tidy), and how to trigger the maintenance scripts from inside Obsidian, see
[`obsidian.md`](obsidian.md).

---

## What to Customize

| Item | How |
|------|-----|
| Pillars | `99-Operations/config.env` → `PILLARS=...`; update Catalog indexes |
| Grade gate | `config.env` → `REFINE_GATE_GRADES=...` (default: `silver gold`) |
| Cron schedules | Edit the `schedule:` field in the relevant `99-Operations/scripts/*.md` note, re-run `render` |
| Script behaviour | Edit the code block in the relevant `99-Operations/scripts/*.md` note, re-run `render`; verify with `reconcile` |
| `~/bin` location | Change `deploy_target` values in script notes if you use a different local bin path |

**Never edit deployed host scripts directly** — they are generated artifacts. Changes
belong in the Layer-0 source note. `reconcile` will catch any drift.

---

## What NOT to Customize Without the Protocol

The following are **constitutional elements** (Tier-0/Tier-1 in `openspec/constitution.md`).
Changing them requires the 4-gate Informed-Upheaval Protocol:

- Three-layer model (Layer 0 / Layer 1 / Layer 2 assignment)
- Deposit-not-merge rule (agents propose; humans gate; scripts execute)
- Grade system (`coal < bronze < silver < gold`)
- No secrets in vault files (INV-7)
- Naming ruleset (INV-11) — changes cascade to the hook, linter, executor, and JSON mirror

If you're confident a change is right, document it as a constitution-override change in
`openspec/changes/` using the template at
`openspec/templates/constitution-override/proposal.md`.

---

## Ongoing Operations

Source `config.env` once per shell session so every script sees the full
configuration (`VAULT_ROOT` plus the vocab variables the linter and refine detector
need):

```bash
. /path/to/my-vault/99-Operations/config.env
```

Then run any operation:

| Task | Command |
|------|---------|
| Lint the vault | `python3 ~/bin/vault-lint.py` |
| Find orphaned Treasury notes | `python3 ~/bin/vault-orphans.py` |
| Slag an effort | Set frontmatter, then `vault-slag.sh <slug>` |
| Dump a husk | `vault-dump.sh <slug>` |
| Re-prospect Tailings | `python3 ~/bin/vault-reprospect.py` |
| Check for drift | `python3 ~/bin/vault-render.py reconcile` |
| Re-deploy after source edit | `python3 ~/bin/vault-render.py render` |

(`vault-slag.sh` and `vault-dump.sh` need only `VAULT_ROOT`; the others read the
vocab variables too — sourcing `config.env` covers all of them.)

---

## Keeping Your Fork in Sync

This template repo evolves. To pull upstream changes without clobbering your vault:

```bash
# In the template repo clone (not your vault)
git remote add upstream https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining.git
git fetch upstream
git merge upstream/main
```

Only `openspec/`, `docs/`, `.github/`, and root files (`README.md`, `LICENSE`, etc.)
are expected to update. The `vault-template/` directory may receive script improvements
— review diffs carefully before applying, especially to `99-Operations/scripts/`.
