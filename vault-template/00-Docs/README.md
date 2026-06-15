# Value Mining — Vault Onboarding

Welcome. This vault is a **Value Mining** operation: a staged, personal knowledge
extraction system that turns raw captures into refined, durable bullion.

This `00-Docs/` folder is the onboarding sandbox. Once you're oriented, you can
delete it — nothing in the pipeline depends on it.

> **Two READMEs, on purpose:** this file is your in-vault getting-started guide;
> `00-Docs/examples/README.md` is a worked Claim→Treasury walkthrough. The *full* fork
> guide and the Obsidian setup guide live in the **template repo** (`memory-mining`)
> under `docs/USING-THIS-TEMPLATE.md` and `docs/obsidian.md` — they intentionally do
> **not** copy into your vault (only `vault-template/`'s contents become the vault).

---

## The Value Chain

```
Capture (20-Claims)
  └─► Prospect ──► Dig ──► Ore ──► Sort ──► Refine ──► 40-Treasury ──► Polish
                                      │
                              ┌───────┴───────────┐
                         Crucible (rare)     Tailings (slag, retain)
                                                   │
                                              Spoil (terminal)
```

| Stage | What happens |
|-------|-------------|
| **Claim** | Raw capture — idea, link, quote, observation. Drop it in `20-Claims/`. |
| **Prospect** | First investigation. Is this worth digging? Create an effort in `30-Sites/`. |
| **Dig** | Active extraction — research, notes, experiments. Work in your Site folder. |
| **Ore** | Digging has produced something. Estimate a grade (`coal/bronze/silver/gold`). |
| **Sort** | 3-way triage: high-grade → Refine; ambiguous/ultra-valuable → Crucible; uneconomic → Tailings; proven false → Spoil. |
| **Refine** | Distill the durable value into a knowledge note in `40-Treasury/`. |
| **Polish** | Perpetual upkeep of high-value bullion. Never "finished." |

**Grade = value only, never effort.** `coal < bronze < silver < gold`.
Auto-refine fires for `silver` and `gold` (configurable in `99-Operations/config.env`).

---

## Folder Layout

```
vault-root/
├── 00-Docs/         ← you are here (deletable)
├── 10-Logbook/      ← daily notes + kanban projection
├── 20-Claims/       ← raw captures + refine pipeline queue/approved
├── 30-Sites/        ← active workings (prospect → dig → ore)
├── 40-Treasury/     ← refined bullion + Catalog MOCs (Layer 1)
├── 50-Mint/         ← future: dated editions (deferred)
├── 60-Forge/        ← future: bespoke wares (deferred)
├── 70-Tailings/     ← slagged ore (retained, re-minable)
├── 71-Spoil/        ← terminal: spent husks + waste
├── 80-Crucible/     ← future: heavy-validation (deferred)
├── 97-Molds/        ← note templates
├── 98-Warehouse/    ← binary attachments
└── 99-Operations/   ← Layer 0: scripts, config, schemas (human-write-only)
```

---

## Three Layers

| Layer | Folder | Nature |
|-------|--------|--------|
| **Layer 0 — Operations** | `99-Operations/` | The mine's machinery. Human-write-only. |
| **Layer 1 — Treasury** | `40-Treasury/` | Refined bullion. Never deleted by automation. |
| **Layer 2 — Workings** | `10-Logbook/`, `20-Claims/`, `30-Sites/`, `70-Tailings/`, `71-Spoil/` | Capture, logs, active/slagged sites. |

---

## Getting Started

### 1. Configure your pillars

Edit `99-Operations/config.env` and set `PILLARS` to your top-level life/knowledge
domains. The vault ships with six pillars as examples — adjust to yours:

```bash
PILLARS="mental health financial social technology calling"
```

Then update (or replace) the Catalog MOCs in `40-Treasury/Catalog/` to match.
The Home MOC (`home-moc.md`) links to each pillar's front door.

### 2. Bootstrap the scripts

Install the dependency into a vault-local venv (modern distros block `pip install`
into the system Python under PEP 668) and render the operational scripts to the host.
First make sure `VAULT_ROOT` in `99-Operations/config.env` is your vault's absolute
path, then:

```bash
cd <vault-root>
python3 -m venv .venv                              # vault-local python
.venv/bin/pip install -r 99-Operations/requirements.txt
. 99-Operations/config.env                         # VAULT_ROOT + vocab + .venv on PATH

# Bootstrap the render script by extracting its code block
# (a meta-script note is Markdown — you can't run the .md directly)
python3 - <<'PY'
import re, os, pathlib, frontmatter
note = pathlib.Path("99-Operations/scripts/render-reconcile.md")
code = re.search(r"^```python\n(.*?)^```", frontmatter.load(note).content, re.S | re.M).group(1)
out = pathlib.Path(os.path.expanduser("~/bin/vault-render.py"))
out.parent.mkdir(parents=True, exist_ok=True); out.write_text(code); out.chmod(0o755)
print("bootstrapped", out)
PY

python3 ~/bin/vault-render.py render               # deploy all scripts
python3 ~/bin/vault_naming.py                      # emit naming-rules.json
git config core.hooksPath 99-Operations/hooks      # activate commit gate
```

For ongoing operations, source `config.env` once per shell session
(`. 99-Operations/config.env`) so every script sees the configuration it needs.

### 3. Create your first daily note

```bash
python3 ~/bin/vault-daily-note.py
```

Or set the cron (see `99-Operations/scripts/daily-note.md` for the schedule).

### 4. Stake your first Claim

Drop a raw note in `20-Claims/` — a quote, a link, an observation.
When ready to investigate, create a Site folder in `30-Sites/<slug>/` with an
`_effort.md` from the mold (`97-Molds/effort.md`).

### 5. Check for drift (ongoing)

```bash
python3 ~/bin/vault-render.py reconcile
```

---

## Seed and Cleanup Scripts

Example data for testing and familiarization is provided via seed/cleanup scripts
stored in `99-Operations/scripts/`. These are intentionally deferred — see the
build PRD (§14) for details. Once built, invoke them as:

```bash
python3 ~/bin/vault-seed.py       # populate with example efforts
python3 ~/bin/vault-cleanup.py    # remove example data
```

---

## Key Invariants (quick reference)

| INV | Rule |
|-----|------|
| INV-1 | Markdown + YAML frontmatter only, UTF-8 |
| INV-2 | Every automated change = exactly one git commit |
| INV-3 | Drift detected, never auto-fixed |
| INV-4 | Agents write only to their Site + `_refine-proposals/` |
| INV-5 | `99-Operations/` is human-write-only |
| INV-6 | Deterministic scripts: no network, no LLM calls |
| INV-7 | No secrets in any vault file |
| INV-9 | Treasury bullion is never deleted by automation |
| INV-11 | All names conform to the naming ruleset (kebab slugs for Treasury/Sites) |
| INV-12 | Pillars are metadata, never folders under `40-Treasury/` |

Full invariant list: `openspec/project.md` (in the template repo) or the build PRD.

---

## Further Reading

- `99-Operations/config.env` — authoritative pillar/grade/stage configuration
- `99-Operations/schemas/frontmatter.md` — all frontmatter schemas
- `99-Operations/scripts/` — all operational scripts (literate format)
- `97-Molds/` — note templates
- `40-Treasury/Catalog/home-moc.md` — master index

In the template repo (`memory-mining`):

- `docs/USING-THIS-TEMPLATE.md` — full fork & setup guide
- `docs/obsidian.md` — recommended Obsidian setup (plugins, settings, running scripts)
- `docs/method.md` — the methodology, incl. promoting a Claim to a Site
