"""Conformance of the corpus's fleet enumerations against the fleet that actually exists.

Three checks govern the Layer-0 fleet, and between them they leave one seam:

    render / reconcile  ->  note -> deployed
    template-parity     ->  template -> live vault
    (nothing)           ->  SPEC -> NOTE

A script can therefore ship, deploy and enforce an invariant while absent from the
specification that governs it — indefinitely, with every build green. That is not
hypothetical: `secret-scan-script.md` (INV-7, ADR-0036, shipped 2026-07-28) reconciles
clean and appears ZERO times in `openspec/specs/maintenance/spec.md`.

An absence has no string to match, so no search-based sweep finds it. Only an enumeration
compared against ground truth does. These tests are that comparison.

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
