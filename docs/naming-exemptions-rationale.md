---
title: "Special File Types & Naming Exemptions"
---

# Special file types & naming exemptions (rationale)

The naming ruleset (`99-Operations/schemas/naming-rules.json`, INV-11; ADR-0015/ADR-0021) requires
content stems to be lowercase kebab-case with ≥3 hyphen-tokens. That rule is for **authored vault
content**, where a descriptive multi-token slug adds human-meaningful specificity. A small set of files
are **not** free to be renamed: an external tool, a git mechanism, or a universal convention depends on
the **exact** string. Renaming them would break function or violate expectations. These are exempt
**by dependency, not by preference** — the list is deliberately narrow, and every entry names what
depends on it. `is_exempt(filename)` (in `vault_naming.py`) is the gate; it matches on the **basename**.

## The classes

### 1. Tool-mandated — agent/memory harness (exact name auto-loaded)
| File | Depends on |
|---|---|
| `CLAUDE.md` | Claude Code loads this exact filename as project instructions at session start |
| `AGENTS.md` | Agent-harness convention: loaded by exact name |
| `MEMORY.md` | Persistent-memory index loaded by exact name |

### 2. Tool-mandated — git
| File | Depends on |
|---|---|
| `.gitignore` | Git reads this exact name |
| `.gitattributes` | Git reads this exact name |
| `.gitkeep` | Convention to retain empty scaffold directories in git |

### 3. Tool-mandated — config (sourced by exact name)
| File | Depends on |
|---|---|
| `config.env` | Sourced by exact path by scripts + bootstrap (the private, gitignored instance) |
| `config.defaults.env` | Sourced first by `config.env` (public framework defaults) |
| `config.env.example` / `*.example` | Standard "copy-to-configure" template convention |

### 4. Tool-mandated — pipeline (date format)
| Glob | Depends on |
|---|---|
| `YYYY-MM-DD.md` (`[0-9]{4}-[0-9]{2}-[0-9]{2}.md`) | Daily-notes plugin + `vault-close-day.py` / `vault-rollover.py` require the ISO date stem (dailies exempt per ADR-0015) |

### 5. Industry convention (human + platform expectation)
| File | Depends on |
|---|---|
| `README.md` | GitHub/GitLab auto-render on folder/repo view; universal reader expectation |
| `LICENSE` / `LICENSE.md` | GitHub license detection + SPDX tooling; legal convention |

## Editor state is out of scope (not an exemption)

`.obsidian/*.json` (Obsidian's own config: `app.json`, `daily-notes.json`, …) is **not** a naming
exemption. Obsidian owns those exact names, but `.obsidian/` is **gitignored** (editor-owned) and the
linter never traverses it, so it falls entirely outside naming governance — no per-name exemption is
needed. (`is_exempt` matches on the basename only; a path-shaped glob would not have worked here anyway.)

## Enforcement note

Mechanical ≥3-token/kebab enforcement remains **deferred** (ADR-0015). The linter (`vault_naming` +
`vault-lint.py`) honors exemptions **now** — any stem matching `exempt_names` (exact) or `exempt_globs`
(basename) is skipped before the kebab/token rules — so that enforcement can later be switched on without
wrongly rejecting a tool-mandated name. The machine-readable lists live in `naming-rules.json`; this doc
is the human rationale (`exempt_rationale_doc`).
