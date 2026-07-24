<!--
SPDX-License-Identifier: Apache-2.0
Copyright 2026 Keith Nielsen
-->

# value-memory-mining

> A professional-grade, spec-driven personal knowledge system built on the
> **Value Mining** methodology — stake Claims, work Sites, grade the Ore, Refine
> high-grade material into lasting Bullion, Polish indefinitely.

[![CI](https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining/actions/workflows/ci.yml/badge.svg)](https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining/actions/workflows/ci.yml)
[![OpenSpec](https://img.shields.io/badge/spec--driven-OpenSpec%20v1.4.1-blue)](openspec/project.md)
[![License](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)
[![Obsidian](https://img.shields.io/badge/vault-Obsidian-7C3AED)](https://obsidian.md)

---

## What Is This?

`value-memory-mining` is two things at once:

1. **A forkable vault template** — copy `vault-template/` and you have a
   production-ready personal knowledge system with working scripts, note templates,
   Catalog indexes, a commit-gate hook, and a documented methodology.

2. **An OpenSpec SDD showcase** — the repository is itself governed by
   [OpenSpec v1.4.1](openspec/project.md): a formal project spec, a constitution with
   constitutional protection, 34 ADRs, 6 capability specs, and a live change-management
   workflow. It demonstrates what a principled, spec-driven personal-tools project
   looks like.

---

## The Value Mining Method

Value Mining treats personal knowledge like a mining operation. Material flows through
a defined pipeline; only high-grade material reaches the Treasury.

```
Capture (20-Claims)
  └─► Dig ──► Ore ──► Sort ──► Refine ──► 40-Treasury ──► Polish
                                      │
                              ┌───────┴───────────┐
                         Crucible (rare)    Tailings (slag, retain)
                                                   │
                                             Spoil (terminal)
```

| Stage | What you do |
|-------|-------------|
| **Claim** | Drop raw captures into `20-Claims/` without evaluation |
| **Dig** | Active extraction — research, notes, experiments |
| **Ore** | Digging produced something; estimate the grade |
| **Sort** | 3-way triage: Refine / Crucible / Tailings / Spoil |
| **Refine** | Distill durable value into a Treasury knowledge note |
| **Polish** | Perpetual upkeep of high-value bullion |

**Grade = value only, never effort.** `coal < bronze < silver < gold`

---

## Three-Layer Architecture

| Layer | Folder | Nature |
|-------|--------|--------|
| **Layer 0 — Operations** | `99-Operations/` | Mine machinery; human-write-only; literate meta-scripts |
| **Layer 1 — Treasury** | `40-Treasury/` | Refined bullion; never deleted by automation |
| **Layer 2 — Workings** | `10-Logbook/`, `20-Claims/`, `30-Sites/`, `70-Tailings/`, `71-Spoil/` | Capture, logs, active/slagged sites |

Agents may only write to their assigned Site and `_refine-proposals/`. Nothing enters
`40-Treasury/` without explicit human approval (the **deposit-not-merge** gate).

---

## System Diagrams

Seven Mermaid diagrams cover the full system — see [`docs/diagrams.md`](docs/diagrams.md).
Render them in Obsidian or any Mermaid-capable viewer.

| # | Diagram | Answers |
|---|---------|---------|
| 1 | Value Chain Overview | End-to-end material flow |
| 2 | Effort Lifecycle | Valid states and transitions |
| 3 | Refine Pipeline (Swimlane) | Who does what; where is the gate? |
| 4 | Sort Router | How ore gets triaged |
| 5 | Folder Stack + Layers | Physical structure by layer and touch frequency |
| 6 | Layer 0 GitOps Loop | How the self-describing Operations layer works |
| 7 | Containment Boundary | What each actor can touch; structurally impossible paths |

---

## Repository Layout

```
2026-AI-Value-Memory-Mining/
├── openspec/                    # OpenSpec SDD (spec-driven project governance)
│   ├── project.md               #   purpose, invariants, standing goals
│   ├── constitution.md          #   constitutional protection + Informed-Upheaval Protocol
│   ├── adr/                     #   34 Architecture Decision Records (ADR-0001–0034)
│   ├── specs/                   #   6 capability specs (vault-structure, value-pipeline, …)
│   └── changes/                 #   change workflow: archive/, live/, templates/
│
├── vault-template/              # Forkable vault skeleton
│   ├── 00-Docs/                 #   onboarding (deletable)
│   ├── 10-Logbook/              #   working area (reserved; framework generates nothing here)
│   ├── 20-Claims/               #   raw captures + refine pipeline queue/approved
│   ├── 30-Sites/                #   active workings
│   ├── 40-Treasury/Catalog/     #   bullion + 7 Catalog indexes (6 pillars + Home)
│   ├── 70-Tailings/             #   slagged ore (retained)
│   ├── 71-Spoil/                #   terminal: spent husks + waste
│   ├── 97-Molds/                #   3 note templates (effort, knowledge, index)
│   ├── 99-Operations/           #   Layer 0: 13 literate meta-scripts + schemas + config
│   └── CLAUDE.md                #   agent conventions for vault operations
│
├── tools/                       # Repo maintenance tools (template-parity.py: mirror completeness check;
│                                #   template-mirror.py: repo→live mirror driver; ship-release.py: guarded
│                                #   tag→Release driver; pr-state.py: per-layer PR reporter)
│
├── docs/                        # Project documentation
│   ├── diagrams.md              #   7 Mermaid system diagrams
│   ├── glossary.md              #   full Value Mining vocabulary
│   ├── method.md                #   method walkthrough (narrative)
│   ├── obsidian.md              #   recommended Obsidian setup + integration
│   ├── research.md              #   background research summary (2026 landscape)
│   └── USING-THIS-TEMPLATE.md  #   fork quick-start guide
│
├── .github/                     # GitHub integration
│   ├── workflows/ci.yml         #   CI: openspec validate + constitution-lint + naming tests + md-lint + scope-review
│   ├── ISSUE_TEMPLATE/          #   bug.yml + change-proposal.yml
│   ├── pull_request_template.md
│   ├── CODEOWNERS
│   └── dependabot.yml
│
├── LICENSE                      # Apache-2.0
├── NOTICE                       # Third-party attribution
├── CONTRIBUTING.md              # Change flow + constitution-override path
├── AGENTS.md                    # AI agent access rules + constitutional hard stop
├── CHANGELOG.md
└── SECURITY.md
```

---

## Constitutional Protection

Fourteen architectural invariants are ordered by criticality band and protected by
`protects:` frontmatter tags on spec files. CI enforces their presence.

| Band | Invariants | Examples |
|------|-----------|---------|
| **Substrate** | INV-1–3 | Format (Markdown+YAML), one-commit-per-op, no-auto-fix |
| **Safety** | INV-4–8, 14 | Agent write scope, Layer 0 ownership, no secrets, offline scripts, **private-by-default** |
| **Value** | INV-9–10 | Treasury immutability, Tailings retention |
| **Consistency** | INV-11–13 | Naming rules, no pillar folders, wikilinks |

**Private by default (INV-14):** a deployed vault never publishes outward. A deny-by-default
`pre-push` guard refuses every push unless you deliberately allowlist a *private* remote
(`PUSH_ALLOWLIST`), and — for Claude Code users — a `PreToolUse` guard blocks the agent from pushing the
vault out and warns loudly before any public publish. Removing it is a Tier-0 constitutional act.

Changing a constitutional element requires the **4-gate Informed-Upheaval Protocol**
(CHECK → PLAN → EXECUTE → RE-CHECK + HUMAN SIGN-OFF). AI agents may draft the first
two gates; the sign-off gate is human-only.

See [`openspec/constitution.md`](openspec/constitution.md) for the full protocol and
[`AGENTS.md`](AGENTS.md) for the verbatim AI-agent hard stop.

---

## Fork Quick-Start

```bash
# 1. Fork this repo on GitHub, then clone
git clone https://github.com/<your-username>/2026-AI-Value-Memory-Mining.git
cd 2026-AI-Value-Memory-Mining

# 2. Copy the vault template
cp -r vault-template/ ~/Documents/my-vault
cd ~/Documents/my-vault

# 3. Configure your pillars
#    Edit 99-Operations/config.env → PILLARS="..."
#    Update 40-Treasury/Catalog/ indexes to match

# 4. Bootstrap
git init
git config core.hooksPath 99-Operations/hooks
python3 -m venv .venv                                # vault-local python (PEP 668)
.venv/bin/pip install -r 99-Operations/requirements.txt
. 99-Operations/config.env                           # VAULT_ROOT + vocab + .venv on PATH

# Bootstrap render, then deploy all scripts
python3 - << 'EOF'
import re, pathlib, frontmatter, os
note = pathlib.Path("99-Operations/scripts/render-reconcile-script.md")
m = re.search(r"^```python\n(.*?)^```", frontmatter.load(note).content, re.S | re.M)
target = pathlib.Path(os.path.expanduser("~/bin/vault-render.py"))
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(m.group(1)); target.chmod(0o755)
EOF

python3 ~/bin/vault-render.py render
python3 ~/bin/vault_naming.py                        # emit naming-rules.json

# 5. Initial commit
git add -A
git commit -m "init: fork from value-memory-mining template"

# 6. Open vault-root in Obsidian and start mining
```

Full walkthrough: [`docs/USING-THIS-TEMPLATE.md`](docs/USING-THIS-TEMPLATE.md)

---

## Operational Scripts (13)

All scripts are stored as literate meta-script notes in
`vault-template/99-Operations/scripts/` and deployed to `~/bin/` via `render`.

| Script | Class | Schedule | Purpose |
|--------|-------|----------|---------|
| `vault_naming.py` | `[script]` | manual | Naming ruleset SSOT; emits `naming-rules.json` |
| `pre-commit` | `[script]` | git hook | Blocks commits with naming-violating filenames |
| `vault-render.py` | `[script]` | manual | Deploy / reconcile Layer-0 scripts |
| `vault-lint.py` | `[script]` | manual | Frontmatter + naming conformance |
| `vault-orphans.py` | `[script]` | manual | Find Treasury notes not linked from any index |
| `vault-refine-detect.py` | `[script]` | `0 6 * * *` | Queue ore that has cleared the grade gate |
| `vault-refine-execute.py` | `[script]` | manual | Apply approved proposals to Treasury |
| `vault-dump.sh` | `[script]` | manual | Move spent husk to Spoil |
| `vault-slag.sh` | `[script]` | manual | Move uneconomic effort to Tailings |
| `vault-reprospect.py` | `[script]` | manual | List slagged efforts for re-evaluation |


---

## The OpenSpec Layer

This repo is governed by [OpenSpec v1.4.1](https://github.com/Fission-AI/OpenSpec)
using the `spec-driven` schema. ADRs are implemented as a project convention alongside
the spec framework (see [ADR-0001](openspec/adr/0001-openspec-as-framework.md)).

| Document | Purpose |
|----------|---------|
| [`openspec/project.md`](openspec/project.md) | Standing goals, 14 invariants, tech stack |
| [`openspec/constitution.md`](openspec/constitution.md) | Constitutional protection, Informed-Upheaval Protocol |
| [`openspec/adr/`](openspec/adr/) | 34 ADRs: framework choice → GitHub rulesets |
| [`openspec/specs/`](openspec/specs/) | 6 capability specs with `protects:` tags |
| [`openspec/changes/`](openspec/changes/) | 14 archived changes, 1 live (deferred), override template |

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Constitutional changes require the
Informed-Upheaval Protocol — use the template at
[`openspec/templates/constitution-override/proposal.md`](openspec/templates/constitution-override/proposal.md).

---

## License

Apache-2.0 — see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

Copyright 2026 Keith Nielsen
