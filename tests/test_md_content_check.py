# SPDX-License-Identifier: Apache-2.0
"""Behaviour of the markdown content-preservation checker.

The load-bearing tests here are the MUTATION cases. A checker that reported
"identical" for everything would pass every formatting test in this file and be
worse than useless, so each formatting test is paired with a mutation that MUST
be caught. The pairing is the point: it is what stops this suite from being a
check that cannot fail.

The mutation in `test_detects_the_real_trailing_space_defect` is not invented --
it is the exact edit `markdownlint --fix` made to
`openspec/specs/naming-rules/spec.md` on 2026-08-27, reproduced here so the
regression has a name.
"""
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import md_content_check as mcc  # noqa: E402


BASE = """# Spec

Some prose that is quite long and will certainly be reflowed by a formatter.

| rule | constraint |
|---|---|
| non-empty | must not be empty |

```
python3 thing.py
```

- **WHEN** called with `trail ` (trailing space)
- **THEN** it exits 1
"""


# --- formatting must be invisible ------------------------------------------------------------

def test_reflow_is_not_a_content_change():
    reflowed = BASE.replace(
        "Some prose that is quite long and will certainly be reflowed by a formatter.",
        "Some prose that is quite long and will\ncertainly be reflowed by a formatter.")
    assert mcc.compare(BASE, reflowed)[0] == "identical"


def test_blank_line_insertion_is_not_a_content_change():
    spaced = BASE.replace("# Spec\n", "# Spec\n\n\n")
    assert mcc.compare(BASE, spaced)[0] == "identical"


def test_table_realignment_is_not_a_content_change():
    aligned = BASE.replace("|---|---|", "| --- | --- |")
    assert mcc.compare(BASE, aligned)[0] == "identical"


def test_fence_language_label_is_not_a_content_change():
    labelled = BASE.replace("```\npython3", "```bash\npython3")
    assert mcc.compare(BASE, labelled)[0] == "identical"


def test_all_four_formatting_changes_at_once_stay_identical():
    combined = (BASE
                .replace("|---|---|", "| --- | --- |")
                .replace("```\npython3", "```bash\npython3")
                .replace("# Spec\n", "# Spec\n\n"))
    assert mcc.compare(BASE, combined)[0] == "identical"


# --- mutations MUST be caught (the half that makes the above meaningful) ----------------------

def test_detects_the_real_trailing_space_defect():
    """The 2026-08-27 regression: MD038 autofix stripped a significant space.

    `trail ` and `trail` are different test inputs -- the first is rejected by
    the validator, the second is VALID -- so this edit inverts the scenario.
    """
    mutated = BASE.replace("`trail `", "`trail`")
    verdict, removed, added = mcc.compare(BASE, mutated)
    assert verdict == "changed"
    assert "`trail" in removed and "`" in removed
    assert "`trail`" in added


def test_detects_a_single_changed_word():
    mutated = BASE.replace("must not be empty", "must not be blank")
    verdict, removed, added = mcc.compare(BASE, mutated)
    assert verdict == "changed"
    assert "empty" in removed and "blank" in added


def test_detects_a_deleted_requirement_line():
    mutated = BASE.replace("- **THEN** it exits 1\n", "")
    assert mcc.compare(BASE, mutated)[0] == "changed"


def test_detects_a_negation_flip():
    mutated = BASE.replace("must not be empty", "must be empty")
    verdict, removed, _ = mcc.compare(BASE, mutated)
    assert verdict == "changed"
    assert "not" in removed


def test_detects_a_changed_number():
    mutated = BASE.replace("exits 1", "exits 0")
    assert mcc.compare(BASE, mutated)[0] == "changed"


@pytest.mark.parametrize("old,new", [
    ("must not be empty", "must not be blank"),
    ("exits 1", "exits 0"),
    ("`trail `", "`trail`"),
    ("**WHEN**", "**IF**"),
])
def test_mutation_matrix_every_mutant_is_killed(old, new):
    """Each mutant is applied in isolation, so attribution is unambiguous."""
    mutated = BASE.replace(old, new)
    assert mutated != BASE, f"mutant {old!r}->{new!r} did not apply; the test is vacuous"
    assert mcc.compare(BASE, mutated)[0] == "changed"


# --- reordering is its own verdict, distinct from loss ---------------------------------------

def test_moved_content_reports_reordered_not_changed():
    """A CHANGELOG consolidation moves entries without losing them.

    Reporting that as 'changed' would have produced exactly the false finding a
    reader made on 2026-09-10 -- the distinction is load-bearing.
    """
    a = "# T\n\n## One\n\nalpha entry\n\n## Two\n\nbeta entry\n"
    b = "# T\n\n## One\n\nbeta entry\n\n## Two\n\nalpha entry\n"
    assert mcc.compare(a, b)[0] == "reordered"


# --- the instrument proves itself -------------------------------------------------------------

def test_selftest_passes():
    assert mcc.selftest() == 0


def test_selftest_is_reachable_from_the_command_line():
    r = subprocess.run([sys.executable, str(REPO / "tools" / "md_content_check.py"),
                        "--selftest"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_structural_tokens_are_classified_but_words_are_not():
    for tok in ("```", "```bash", "|---|---|", "| --- |", "|", "-", "*"):
        assert mcc.is_structural(tok), tok
    for tok in ("empty", "`trail", "**WHEN**", "1", "not"):
        assert not mcc.is_structural(tok), tok


def test_bullet_style_change_is_not_a_content_change():
    """MD004/ul-style swaps `-` for `*`; that is formatting, not content."""
    a = "# T\n\n- one\n- two\n"
    b = "# T\n\n* one\n* two\n"
    assert mcc.compare(a, b)[0] == "identical"


def test_documents_the_standalone_dash_blind_spot():
    """The tool's ONE known miss, pinned so it cannot silently widen.

    A standalone dash is structural, so removing only that dash is invisible.
    This test asserts the blind spot's exact shape: the dash alone is missed,
    while a word removed alongside it is still caught.
    """
    a = "# T\n\nalpha - beta\n"
    b = "# T\n\nalpha beta\n"
    assert mcc.compare(a, b)[0] == "identical", "blind spot changed shape"

    # ...but the moment real words differ, detection resumes.
    c = "# T\n\nalpha gamma\n"
    assert mcc.compare(a, c)[0] == "changed"


def test_malformed_range_exits_two_not_a_traceback():
    r = subprocess.run([sys.executable, str(REPO / "tools" / "md_content_check.py"),
                        "--repo", str(REPO), "--base", "no-such-ref-xyz",
                        "--head", "also-missing-xyz"],
                       capture_output=True, text=True)
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    assert "Traceback" not in r.stderr
