"""Conformance of the corpus's fleet enumerations against the fleet that actually exists.

Three checks govern the Layer-0 fleet, and between them they leave one seam:

    render / reconcile  ->  note -> deployed vault
    template-parity     ->  template -> live vault
    (nothing)           ->  SPEC -> NOTE
    (nothing)           ->  NOTE -> THIS REPO'S OWN .claude/hooks/ COPY   <- F29, closed below

A script can therefore ship, deploy and enforce an invariant while absent from the
specification that governs it — indefinitely, with every build green. That is not
hypothetical: `secret-scan-script.md` (INV-7, ADR-0036, shipped 2026-07-28) reconciles
clean and appears ZERO times in `openspec/specs/maintenance/spec.md`.

An absence has no string to match, so no search-based sweep finds it. Only an enumeration
compared against ground truth does. These tests are that comparison.

The fourth seam (F29) is the same shape one layer out. This repository carries its OWN tracked
copy of each harness hook under `.claude/hooks/`, because a Claude Code session rooted here loads
hooks from this directory and cannot read a literate note. Those copies are governed by nothing:
`render`/`reconcile` govern note -> *deployed vault*, and `template-parity` governs template ->
*live vault*. Neither reaches this repo's own copies.

That is not hypothetical either. It cost twice on 2026-08-26 alone: first the hook was registered
in `.claude/settings.json` pointing at a file that did not yet exist -- and a hook whose command
fails DEFERS SILENTLY, so the failure reads as success -- and later a note's implementation block
was edited while the rendered copy went stale, with the full suite green throughout.

Note also what the guard suite itself says: `test_gh_invocation_guard.py` extracts the code from
the NOTE precisely because `.claude/hooks/` "may be stale or absent". Seventeen green tests there
therefore say nothing whatever about the file the harness actually loads.

Both directions are asserted on purpose. A check that detects only omissions passes on a
table naming a script deleted a month ago.

Ground truth is the note set on disk — never a literal list here, which would be one more
hand-maintained duplicate of a machine-checkable fact and would drift the same way.
"""
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]
NOTES_DIR = REPO / "vault-template" / "99-Operations" / "scripts"
MAINTENANCE_SPEC = REPO / "openspec" / "specs" / "maintenance" / "spec.md"
README = REPO / "README.md"
USING = REPO / "docs" / "USING-THIS-TEMPLATE.md"

# A table row naming a script note: | `<stem>-script.md` | ...
ROW_NOTE = re.compile(r"^\|\s*`([a-z0-9-]+-script\.md)`\s*\|", re.M)


def note_set():
    """The fleet that exists, read from disk. The denominator for every check below."""
    return {p.name for p in NOTES_DIR.glob("*-script.md")}


def _frontmatter_field(note_path, field):
    """Read a top-level frontmatter scalar without importing a YAML parser."""
    m = re.search(rf"^{field}:\s*(.+?)\s*$", note_path.read_text(), re.M)
    return m.group(1).strip().strip("\"'") if m else None


# --------------------------------------------------------------------------------------
# A1.1 / A1.2 — the enumerations name exactly the note set, and their counts agree
# --------------------------------------------------------------------------------------

def test_ground_truth_is_discoverable():
    """Guard the guard: if the note set cannot be read, every test below passes vacuously."""
    notes = note_set()
    assert notes, f"no script notes found under {NOTES_DIR} — the other assertions would be vacuous"
    assert len(notes) >= 10, f"implausibly small fleet ({len(notes)}); ground truth is likely broken"


def test_maintenance_spec_inventory_names_exactly_the_note_set():
    listed = set(ROW_NOTE.findall(MAINTENANCE_SPEC.read_text()))
    notes = note_set()

    missing = notes - listed          # shipped but ungoverned
    phantom = listed - notes          # governed but nonexistent

    assert not missing, (
        f"{len(missing)} script note(s) exist but have NO row in the maintenance Script "
        f"Inventory: {sorted(missing)}. A shipped script absent from the spec that governs "
        f"it is the seam this test exists to close."
    )
    assert not phantom, (
        f"{len(phantom)} row(s) in the maintenance Script Inventory name a note that does "
        f"not exist: {sorted(phantom)}. An inventory that only detects omissions passes on a "
        f"table naming a script deleted a month ago."
    )


def test_readme_inventory_names_exactly_the_note_set():
    """The README lists deployed artifacts, so compare on the artifact each note deploys."""
    text = README.read_text()
    section = text[text.index("## Operational Scripts"):]
    section = section[:section.index("\n## ", 1)] if "\n## " in section[1:] else section

    listed = set(re.findall(r"^\|\s*`([A-Za-z0-9_.-]+)`\s*\|", section, re.M))
    targets = {
        pathlib.PurePosixPath(t).name
        for t in (_frontmatter_field(p, "deploy_target") for p in NOTES_DIR.glob("*-script.md"))
        if t
    }

    missing = targets - listed
    phantom = listed - targets

    assert not missing, (
        f"{len(missing)} deployed artifact(s) missing from the README table: {sorted(missing)}"
    )
    assert not phantom, (
        f"{len(phantom)} README row(s) name an artifact nothing deploys: {sorted(phantom)}"
    )


def test_readme_stated_count_equals_its_own_rows():
    """A heading that disagrees with the table beneath it is wrong twice, in two directions."""
    text = README.read_text()
    stated = int(re.search(r"^## Operational Scripts \((\d+)\)", text, re.M).group(1))

    section = text[text.index("## Operational Scripts"):]
    section = section[:section.index("\n## ", 1)] if "\n## " in section[1:] else section
    rows = len(re.findall(r"^\|\s*`[A-Za-z0-9_.-]+`\s*\|", section, re.M))

    assert stated == rows, (
        f"README heading states {stated} operational scripts; its own table presents {rows} rows"
    )
    assert stated == len(note_set()), (
        f"README heading states {stated}; the fleet has {len(note_set())} notes"
    )


# --------------------------------------------------------------------------------------
# A1.4 — declared cadence matches declared runtime
# --------------------------------------------------------------------------------------

CRON_EXPR = re.compile(r"`[\d*/,-]+\s+[\d*/,-]+\s+[\d*/,-]+\s+[\d*/,-]+\s+[\d*/,-]+`")


def test_no_note_declares_a_cron_runtime_or_schedule():
    """The premise the two tests below rest on. `render` installs no schedules."""
    offenders = []
    for p in sorted(NOTES_DIR.glob("*-script.md")):
        if _frontmatter_field(p, "schedule") is not None:
            offenders.append(f"{p.name}: declares schedule:")
        if (_frontmatter_field(p, "runtime") or "") == "cron":
            offenders.append(f"{p.name}: declares runtime: cron")
    assert not offenders, "notes declaring an uninstallable cadence: " + "; ".join(offenders)


def test_no_live_document_states_a_cron_schedule():
    """A cadence a script cannot honour is a decorative declaration."""
    offenders = []
    for doc in (README, MAINTENANCE_SPEC):
        for i, line in enumerate(doc.read_text().splitlines(), 1):
            if CRON_EXPR.search(line) and "script" in line:
                offenders.append(f"{doc.relative_to(REPO)}:{i}: {line.strip()[:90]}")
    assert not offenders, (
        "live document(s) state a schedule for a script whose note declares no cron runtime; "
        "`render` deploys code and marks it executable, it installs no schedules:\n  "
        + "\n  ".join(offenders)
    )


def test_no_document_instructs_editing_the_schedule_field():
    """Instructing a reader to edit an unread field teaches that the docs are approximate."""
    offenders = [
        f"{USING.relative_to(REPO)}:{i}: {line.strip()[:90]}"
        for i, line in enumerate(USING.read_text().splitlines(), 1)
        if "`schedule:`" in line and "Edit" in line
    ]
    assert not offenders, (
        "document(s) instruct editing a `schedule:` field that nothing reads:\n  "
        + "\n  ".join(offenders)
    )


# --------------------------------------------------------------------------------------
# F29 — this repo's own hook copies against the notes that are their source of truth
#
# Ground truth is the hook set on disk, matching this module's existing discipline: never a
# literal list here, which would be one more hand-maintained duplicate that drifts the same way.
# --------------------------------------------------------------------------------------

HOOKS_DIR = REPO / ".claude" / "hooks"

# The implementation block of a literate meta-script note (INV-3). First block wins, which is the
# same rule `render` and `.github/scripts/validate-scripts.sh` already apply.
PY_BLOCK = re.compile(r"^```python\n(.*?)^```", re.S | re.M)


def hook_set():
    """The harness hooks this repository actually ships. The denominator for the checks below."""
    return sorted(HOOKS_DIR.glob("*.py"))


def test_hook_ground_truth_is_discoverable():
    """Guard the guard: with no hooks found, the parity assertion below passes vacuously."""
    hooks = hook_set()
    assert hooks, (
        f"no hook files found under {HOOKS_DIR.relative_to(REPO)} — the parity assertion "
        f"would pass vacuously. If the hooks were deliberately removed, delete this test with them."
    )


def parity_report(hooks_dir, notes_dir):
    """Compare a hook directory against its notes. Pure: takes its subjects, touches no globals.

    Factored this way deliberately. A check whose failure branches can only be reached by
    mutating the live `.claude/` is a check whose failure branches never get tested — and an
    assertion nobody has watched fail is an assumption wearing a test's clothes.

    Returns (drift, unnoted) as lists of human-readable strings.
    """
    drift, unnoted = [], []

    for hook in sorted(pathlib.Path(hooks_dir).glob("*.py")):
        note = pathlib.Path(notes_dir) / f"{hook.stem}-script.md"
        if not note.exists():
            unnoted.append(f"{hook.name} -> expected {note.name}")
            continue

        block = PY_BLOCK.search(note.read_text(encoding="utf-8"))
        if block is None:
            unnoted.append(f"{note.name} has no ```python implementation block")
            continue

        if block.group(1) != hook.read_text(encoding="utf-8"):
            drift.append(f"{hook.name} differs from {note.name} — re-render it; "
                         f"the note is the source of truth (INV-3)")

    return drift, unnoted


def test_each_repo_hook_is_byte_identical_to_its_note():
    """F29: the file the harness LOADS must match the note that governs it.

    A registered hook pointing at stale code is undetectable from the outside: the harness runs
    whatever is on disk, and a passing test suite that reads the note instead proves nothing
    about it.
    """
    drift, unnoted = parity_report(HOOKS_DIR, NOTES_DIR)

    # Reported together: fixing one and re-running to discover the other wastes a cycle.
    assert not unnoted, (
        f"{len(unnoted)} hook file(s) governed by NO note — a shipped control with no literate "
        f"source is exactly what INV-3 forbids:\n  " + "\n  ".join(unnoted)
    )
    assert not drift, (
        f"{len(drift)} hook file(s) have DRIFTED from their note. The harness loads the file, "
        f"not the note, so this drift is live:\n  " + "\n  ".join(drift)
    )


# -- the failure branches, exercised against fixtures rather than the live repo ----------

NOTE_STUB = "# note\n\n## Implementation\n\n```python\n{body}```\n"


def _fixture(tmp_path, hook_body, note_body=None, note_name=None):
    hooks, notes = tmp_path / "hooks", tmp_path / "notes"
    hooks.mkdir(); notes.mkdir()
    (hooks / "probe-guard.py").write_text(hook_body, encoding="utf-8")
    if note_body is not None:
        notes.joinpath(note_name or "probe-guard-script.md").write_text(
            NOTE_STUB.format(body=note_body), encoding="utf-8")
    return hooks, notes


def test_parity_report_is_silent_when_hook_matches_its_note(tmp_path):
    """The confirming case — asserted so the failure cases below are not vacuously red."""
    drift, unnoted = parity_report(*_fixture(tmp_path, "x = 1\n", "x = 1\n"))
    assert (drift, unnoted) == ([], [])


def test_parity_report_detects_a_stale_hook(tmp_path):
    """The drift that actually occurred on 2026-08-26: note edited, rendered copy left behind."""
    drift, unnoted = parity_report(*_fixture(tmp_path, "x = 1\n", "x = 2\n"))
    assert unnoted == []
    assert len(drift) == 1 and "differs from" in drift[0]


def test_parity_report_detects_a_hook_with_no_note(tmp_path):
    """A hook shipped with no literate source — INV-3's own prohibition, and it must fail CLOSED."""
    drift, unnoted = parity_report(*_fixture(tmp_path, "x = 1\n", note_body=None))
    assert drift == []
    assert len(unnoted) == 1 and "expected probe-guard-script.md" in unnoted[0]


def test_parity_report_detects_a_note_with_no_implementation_block(tmp_path):
    """A note that governs nothing extractable is not a source of truth, and must not pass."""
    hooks, notes = _fixture(tmp_path, "x = 1\n", "x = 1\n")
    notes.joinpath("probe-guard-script.md").write_text("# note, prose only\n", encoding="utf-8")
    drift, unnoted = parity_report(hooks, notes)
    assert drift == []
    assert len(unnoted) == 1 and "no ```python implementation block" in unnoted[0]
