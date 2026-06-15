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

Optional for Phase 3 (agent operations, deferred):
- [Hermes Agent v0.15.2](https://github.com/Nous-Research/hermes) — Kanban worker runtime
- [n8n](https://n8n.io) — Orchestration / egress-control layer
- [Ollama](https://ollama.ai) — Local model inference

---

## Fork and Clone

```bash
# Fork on GitHub, then:
git clone https://github.com/<your-username>/memory-mining.git my-vault
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
git commit -m "init: fork from memory-mining template"
```

---

## Step 2: Configure Your Pillars

Edit `99-Operations/config.env`:

```bash
# Replace with your own top-level life/knowledge domains
PILLARS="mental health financial social technology calling"
```

Pillar design principles:
- **Distinct**: minimal overlap between pillars
- **Top-level**: no pillar should be a sub-category of another
- **Durable**: stable for years, not months

Then update `40-Treasury/Catalog/` to match. Either rename the example MOC files or
create new ones from `97-Molds/moc.md`. The Home MOC (`home-moc.md`) should link to
each of your pillar MOCs.

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
note = pathlib.Path("99-Operations/scripts/render-reconcile.md")
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

## Step 5: Set Up Crons (Optional)

Three scripts run on a schedule. Each must see the full vault configuration, so
**source `config.env` first** — it exports `VAULT_ROOT` plus the vocab variables
(`PILLARS`, `GRADES`, `REFINE_GATE_GRADES`, …) that the scripts read. Setting only
`VAULT_ROOT` will make `vault-refine-detect.py` fail with a missing-variable error.

Add them to your crontab (`crontab -e`), pointing at your vault's `config.env`:

```cron
# daily note at 00:01
1 0 * * * . /path/to/my-vault/99-Operations/config.env && python3 ~/bin/vault-daily-note.py

# roll-over carry-over links at 00:02
2 0 * * * . /path/to/my-vault/99-Operations/config.env && python3 ~/bin/vault-rollover.py

# refine detector at 06:00
0 6 * * * . /path/to/my-vault/99-Operations/config.env && python3 ~/bin/vault-refine-detect.py
```

Make sure `VAULT_ROOT` inside `config.env` is set to the absolute path of your vault
(Step 2). Sourcing `config.env` then provides everything each script needs.

---

## Step 6: Open in Obsidian

Open the vault folder in Obsidian. You'll find:

- `00-Docs/README.md` — orientation and getting-started guide (deletable after setup)
- `40-Treasury/Catalog/home-moc.md` — master index linking to your pillar MOCs
- `97-Molds/` — note templates (daily, effort, knowledge, moc)
- `99-Operations/` — all scripts and config (human-write-only)

For the recommended plugins, settings (incl. the default-new-note-location that keeps
your inbox tidy), and how to trigger the maintenance scripts from inside Obsidian, see
[`obsidian.md`](obsidian.md).

---

## What to Customize

| Item | How |
|------|-----|
| Pillars | `99-Operations/config.env` → `PILLARS=...`; update Catalog MOCs |
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
`openspec/changes/templates/constitution-override/proposal.md`.

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
| Create today's daily note | `python3 ~/bin/vault-daily-note.py` |
| Lint the vault | `python3 ~/bin/vault-lint.py` |
| Find orphaned Treasury notes | `python3 ~/bin/vault-orphans.py` |
| Render kanban board | `python3 ~/bin/vault-kanban-render.py` |
| Slag an effort | Set frontmatter, then `vault-slag.sh <slug>` |
| Dispose a husk | `vault-dispose.sh <slug>` |
| Re-prospect Tailings | `python3 ~/bin/vault-reprospect.py` |
| Check for drift | `python3 ~/bin/vault-render.py reconcile` |
| Re-deploy after source edit | `python3 ~/bin/vault-render.py render` |

(`vault-slag.sh` and `vault-dispose.sh` need only `VAULT_ROOT`; the others read the
vocab variables too — sourcing `config.env` covers all of them.)

---

## Keeping Your Fork in Sync

This template repo evolves. To pull upstream changes without clobbering your vault:

```bash
# In the template repo clone (not your vault)
git remote add upstream https://github.com/keith-nielsen/memory-mining.git
git fetch upstream
git merge upstream/main
```

Only `openspec/`, `docs/`, `.github/`, and root files (`README.md`, `LICENSE`, etc.)
are expected to update. The `vault-template/` directory may receive script improvements
— review diffs carefully before applying, especially to `99-Operations/scripts/`.
