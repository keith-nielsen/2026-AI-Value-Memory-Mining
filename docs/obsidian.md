---
title: "Obsidian Integration"
---

# Obsidian Integration

A Value Mining vault is plain Markdown + YAML frontmatter under git, so it works with
**any** editor — all 13 scripts and the whole pipeline are editor-agnostic. But
[Obsidian](https://obsidian.md) is the recommended surface: it renders frontmatter as
a Properties form, resolves `[[wikilinks]]`, and instantiates the molds. This guide
covers the recommended setup and how Obsidian relates to the deterministic scripts.

> Obsidian is **optional**. If you prefer VS Code / vim, the CLI workflow in
> [`USING-THIS-TEMPLATE.md`](USING-THIS-TEMPLATE.md) is complete on its own.

---

## Open the vault

**"Open folder as vault" → your vault directory** (e.g. `~/Documents/Vault`). Do *not*
"Create new vault" — the vault already exists. Obsidian hides dot-folders, so `.git`,
`.venv`, and `99-Operations/hooks` won't clutter the file tree.

---

## Recommended core plugins

All built in — no community plugins required for the core workflow.

| Plugin | Why |
|--------|-----|
| **Templates** | Instantiate the `97-Molds/` molds (effort / knowledge / moc) |
| **Daily Notes** | Create/open today's daily note from `97-Molds/daily.md` |
| **Bookmarks** | Pin `40-Treasury/Catalog/home-moc.md` as your front door |
| **Outline**, **Backlinks** | Navigation; Backlinks surfaces what links to a note |

Properties (the frontmatter UI) is built in and always on.

---

## Settings that matter

| Setting | Value | Why |
|---------|-------|-----|
| Files & Links → **Default location for new notes** | **`20-Claims`** | New / dangling-link notes land in the *inbox*, never the vault root. Prevents stray fragments. |
| Editor → **Properties in document** | Visible | See/edit frontmatter inline |
| Templates → **Template folder location** | `97-Molds` | Where the molds live |
| Daily Notes → **Template** / **New file location** / **Format** | `97-Molds/daily.md` / `10-Logbook/Daily` / `YYYY-MM-DD` | Match the `vault-daily-note.py` output exactly |

The default-new-note-location setting is the single most important one: without it, a
click on an unresolved `[[wikilink]]` creates an empty note at the vault **root**, which
is outside the Value Mining structure and becomes clutter.

---

## Creating notes (native — no scripts)

- **Effort / knowledge / moc notes:** Templates plugin → "Insert template" → pick the
  mold. The full, correct frontmatter schema drops in and `{{date}}` is filled. You
  never hand-build frontmatter. (See also [Adding Properties](#adding-properties-to-a-new-note).)
- **Daily notes:** Daily Notes plugin, configured as above. Produces the same file
  `vault-daily-note.py` / cron would — interchangeable and idempotent.

Only the daily note is scripted. The effort/knowledge/moc molds were always meant for
human instantiation in Obsidian.

### Adding Properties to a new note

Easiest first: (1) instantiate a mold (brings the whole schema); (2) command palette →
"Add file property", set `pillars` to a **List** and type — Obsidian autocompletes from
existing pillar values; (3) paste from `99-Operations/schemas/frontmatter.md`.

---

## Running the maintenance scripts from Obsidian (optional)

The deterministic scripts (`lint`, `kanban-render`, `reconcile`, `orphans`, …) normally
run from the CLI or cron. To trigger them from inside Obsidian, use the community
**Shell Commands** plugin — with one wrinkle if Obsidian is a **Flatpak**:

A Flatpak sandbox can't see the host `python3` + `frontmatter` or `~/bin`, so you must
bounce to the host. Grant host access once:

```bash
flatpak override --user --talk-name=org.freedesktop.Flatpak md.obsidian.Obsidian
```

Then define commands like:

```
flatpak-spawn --host bash -lc '. ~/Documents/Vault/99-Operations/config.env && python3 ~/bin/vault-kanban-render.py'
```

Bind them to hotkeys. Good candidates: `kanban-render`, `lint`, `reconcile`, `orphans`.
All are **gate-safe** — none bypass the human approval step, and the commit-gate hook
(INV-11) still fires on any commit they make.

---

## Environment notes (Linux + Flatpak)

- **Install:** `flatpak install --user flathub md.obsidian.Obsidian`, then grant the
  vault path: `flatpak override --user --filesystem=$HOME/Documents md.obsidian.Obsidian`.
- **NVIDIA + Flatpak GPU:** the Flatpak's NVIDIA GL userspace must match the host kernel
  driver **exactly**. A mismatch (e.g. host `595.71.05` but the flatpak shipping
  `nvidia-590-48-01`) makes GL init fail — `EGL_NOT_INITIALIZED`, "Exiting GPU process",
  and a fallback to software rendering. Fix by installing the matching extension:
  `flatpak install flathub org.freedesktop.Platform.GL.nvidia-595-71-05` (plus the
  `GL32` variant), then relaunch. The other launch-time messages (dbus system bus,
  `xdg-settings`, `xapp-gtk3-module`, first-run `ENOENT`) are benign sandbox noise.

---

## Roadmap / deferred ideas

- **Claim inbox as a punch-list table with a one-click "promote to Site" button.**
  Picture `20-Claims/` rendered (Dataview) as a table, each row with a button that
  promotes the claim to a `30-Sites/<slug>/_effort.md` and cleans up behind itself.
  Building blocks: a deterministic `vault-promote.sh` (the CLI backbone — create dir,
  instantiate the effort mold, migrate the body, remove the claim, one commit) fronted
  by an Obsidian Buttons/Shell-Commands UI. Until then, see
  [Promoting a Claim to a Site](method.md#promoting-a-claim-to-a-site) for the manual
  procedure.
- **Stray-fragment lint** — flag root-level notes, claims carrying an effort `status`
  field (promotion-pending), and dangling wikilinks.
- **`99-Operations` index MOC** — one browsable note listing the 13 scripts with
  one-line purposes.
