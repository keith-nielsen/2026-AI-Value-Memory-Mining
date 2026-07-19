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
| **Templates** | Instantiate the `97-Molds/` molds (effort / knowledge / index) |
| **Bookmarks** | Pin `40-Treasury/Catalog/home-master-index.md` as your front door |
| **Outline**, **Backlinks** | Navigation; Backlinks surfaces what links to a note |

Properties (the frontmatter UI) is built in and always on.

---

## Settings that matter

| Setting | Value | Why |
|---------|-------|-----|
| Files & Links → **Automatically update internal links** | **OFF** | ⚠️ **Critical — see below.** Renames are governed; Obsidian's silent auto-relinking conflicts with the naming ceremony (INV-3). |
| Files & Links → **Default location for new notes** | **`20-Claims`** | New / dangling-link notes land in the *inbox*, never the vault root. Prevents stray fragments. |
| Editor → **Properties in document** | Visible | See/edit frontmatter inline |
| Templates → **Template folder location** | `97-Molds` | Where the molds live |

> ### ⚠️ Turn OFF "Automatically update internal links"
>
> This vault is **governed**: renaming a file or note is a *naming change* that runs the OpenSpec
> ceremony (propose → apply → Gate-4 → **mirror**) so links are retargeted **deliberately and
> reviewably**. Obsidian's "Automatically update internal links" does the opposite — on any rename it
> **silently rewrites every `[[wikilink]]` across the vault**. That:
> - violates **INV-3** (drift is *detected* via `reconcile`, **never auto-fixed**),
> - bypasses the governed naming ceremony (un-reviewed mass edits), and
> - can spray an un-ratified naming scheme across the vault from a single GUI rename.
>
> Keep it **off**; let renames go through the ceremony. This is the single most important Obsidian
> setting for a governed vault.

The default-new-note-location setting is the next most important: without it, a
click on an unresolved `[[wikilink]]` creates an empty note at the vault **root**, which
is outside the Value Mining structure and becomes clutter.

---

## Creating notes (native — no scripts)

- **Effort / knowledge / index notes:** Templates plugin → "Insert template" → pick the
  mold. The full, correct frontmatter schema drops in and `{{date}}` is filled. You
  never hand-build frontmatter. (See also [Adding Properties](#adding-properties-to-a-new-note).)
**On daily notes.** The framework retired its own daily note and close cycle (ADR-0032) and
ships no daily mold. `10-Logbook/` is a working area: if you want a dated journal there, enable
the **Daily Notes** plugin with your own template — the naming rules still exempt `YYYY-MM-DD.md`
stems, so the commit-gate will accept them. Nothing in the pipeline reads it.

The effort/knowledge/index molds were always meant for human instantiation in Obsidian.

### Adding Properties to a new note

Easiest first: (1) instantiate a mold (brings the whole schema); (2) command palette →
"Add file property", set `pillars` to a **List** and type — Obsidian autocompletes from
existing pillar values; (3) paste from `99-Operations/schemas/note-frontmatter-schema.md`.

---

## Running the maintenance scripts from Obsidian (optional)

The deterministic scripts (`lint`, `reconcile`, `orphans`, …) normally
run from the CLI or cron. To trigger them from inside Obsidian, use the community
**Shell Commands** plugin — with one wrinkle if Obsidian is a **Flatpak**:

A Flatpak sandbox can't see the host `python3` + `frontmatter` or `~/bin`, so you must
bounce to the host. Grant host access once:

```bash
flatpak override --user --talk-name=org.freedesktop.Flatpak md.obsidian.Obsidian
```

Then define commands like:

```
flatpak-spawn --host bash -lc '. ~/Documents/Vault/99-Operations/config.env && python3 ~/bin/vault-lint.py'
```

Bind them to hotkeys. Good candidates: `lint`, `reconcile`, `orphans`.
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

- **"Start a Dig" — a one-click Claim→Site flow.** Picture `20-Claims/` rendered
  (Dataview) as a punch-list table, each row a *nugget to chew*, with a button that
  lifts the nugget out of the inbox and into a Site to begin digging. The deterministic
  backbone is a `vault-promote.sh` that:
  1. creates `30-Sites/<slug>/<slug>.md` from the `effort` mold;
  2. moves the Claim body in as the seed of the **Dig** section;
  3. **prefills the frontmatter dates** — `started:` = today; the original capture date
     is recovered from, in order: the Claim's `captured:` frontmatter → its **git
     first-add date** (`git log --diff-filter=A --format=%ad -- <claim>`) → filesystem
     ctime. This is what lets Claims stay *raw and date-less*: git already records when
     the nugget landed, so the promote flow reads it back out (no manual dating needed);
  4. carries over `pillars:` if present;
  5. removes the Claim (single source of truth) — one commit, commit-gate validates the name.
  An Obsidian Buttons/Shell-Commands UI fronts it. Until then, see
  [Promoting a Claim to a Site](method.md#promoting-a-claim-to-a-site) for the manual
  procedure.
- **Stray-fragment lint** — flag root-level notes, claims carrying an effort `status`
  field (promotion-pending), and dangling wikilinks.
- **`99-Operations` index index** — one browsable note listing the 13 scripts with
  one-line purposes.
