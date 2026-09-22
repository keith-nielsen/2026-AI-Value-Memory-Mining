"""Every script path named in a harness settings file resolves to a real deploy target.

An exclusion entry is matched as an EXACT STRING. When the artifact it names moves or is
retired, the entry does not error — it silently ceases to match, and the resulting refusal
is indistinguishable from a genuine denial. That false negative is what the SE-5 probe was
built to detect.

Nothing else in this repository observes it: `excludedCommands` appears nowhere in tests/,
.github/ or tools/, and the fleet's own tests invoke scripts as subprocesses, so they never
traverse the harness. An exclusion can be broken while every test reports green.

STATED LIMIT — read before trusting this file:

    These tests establish that a named path RESOLVES to something the fleet deploys.
    They CANNOT establish that the exclusion MATCHES at the harness layer, because no
    automated test traverses Claude Code. Only a real agent invocation confirms that, and
    it is therefore an operator step, not a gate.

    A check that appears to cover the harness and does not is worse than no check, which is
    why the limit is written here rather than left to be discovered.
"""
import json
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]
NOTES_DIR = REPO / "vault-template" / "99-Operations" / "scripts"

SETTINGS_FILES = [
    REPO / ".claude" / "settings.json",
    REPO / "vault-template" / ".claude" / "settings.json",
]

SCRIPT_PATH = re.compile(r"[\w$./~{}-]+\.(?:py|sh)")


def deploy_targets():
    """Ground truth: the FULL declared deploy_target of each note, not just its basename."""
    out = set()
    for note in NOTES_DIR.glob("*-script.md"):
        m = re.search(r"^deploy_target:\s*(.+?)\s*$", note.read_text(), re.M)
        if m:
            out.add(m.group(1).strip().strip("\"'"))
    return out


def script_paths_in(settings_path):
    """Every .py/.sh path appearing anywhere in a settings file, with its JSON location."""
    found = []

    def walk(node, where):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{where}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{where}[{i}]")
        elif isinstance(node, str):
            for hit in SCRIPT_PATH.findall(node):
                found.append((where, hit))

    walk(json.loads(settings_path.read_text()), "")
    return found


def test_ground_truth_is_discoverable():
    """Guard the guard: with no deploy targets, every assertion below passes vacuously."""
    targets = deploy_targets()
    assert targets, f"no deploy_target found under {NOTES_DIR} — assertions would be vacuous"


def _normalise(raw):
    """Strip the harness variable prefix and any leading ./ so a declared path can be
    compared by its PATH, not merely by its last component."""
    s = raw.strip().strip('"').strip("'")
    for prefix in ("$CLAUDE_PROJECT_DIR/", "${CLAUDE_PROJECT_DIR}/", "./"):
        if s.startswith(prefix):
            s = s[len(prefix):]
    return s


def test_every_settings_script_path_resolves_to_a_deploy_target():
    """Compared by PATH SUFFIX, never by basename.

    ⚠ The first cut of this test compared basenames, and was measured FALSE-NEGATIVE on
    2026-08-18: with the exclusion still naming `~/bin/vault-refine-execute.py` while the
    deploy target had moved to `99-Operations/bin/vault-refine-execute.py`, it PASSED. The
    two differ in every component except the last — which is precisely the mismatch this
    test exists to catch, and precisely what a relocation produces.

    A suffix match still tolerates a legitimate absolute or variable-rooted prefix
    (`$CLAUDE_PROJECT_DIR/...`) while refusing a path that lives somewhere else entirely.
    """
    targets = deploy_targets()
    unresolved = []

    for settings in SETTINGS_FILES:
        if not settings.exists():
            continue
        for where, raw in script_paths_in(settings):
            candidate = _normalise(raw)
            if not any(candidate == t or candidate.endswith("/" + t) for t in targets):
                unresolved.append(
                    f"{settings.relative_to(REPO)} at {where}: {raw!r} "
                    f"matches no declared deploy_target by path"
                )

    assert not unresolved, (
        f"{len(unresolved)} settings path(s) name an artifact that no script note deploys. "
        f"An exclusion is an exact string match: when its artifact moves, the entry does not "
        f"error, it stops matching, and the refusal is indistinguishable from a real deny.\n  "
        + "\n  ".join(unresolved)
    )


def test_at_least_one_settings_file_declares_a_script_path():
    """Without this, the test above passes on a settings file that names nothing at all —
    which is exactly how a check comes to assert nothing after an unrelated refactor."""
    total = sum(len(script_paths_in(s)) for s in SETTINGS_FILES if s.exists())
    assert total > 0, (
        "no settings file declares any script path; the resolution test above would pass "
        "vacuously"
    )


# --- item 38: the seed template carries the GitHub read-hosts -------------------------------------

TEMPLATE_SETTINGS = REPO / "vault-template" / ".claude" / "settings.json"


def test_seed_template_carries_the_github_read_hosts():
    """Item 38: a vault deployed from the template must not start one denied prompt away from losing
    GitHub reads. `allowedDomains` is NOT mere prompt-suppression — a denied prompt becomes a
    session-scoped deny, and one denied api.github.com prompt kills gh's anonymous reads for the rest
    of the session (the capability probe, pr-flow --plan reads, gh_read's fallback). settings.json is
    SEED (not lockstep), so template-parity cannot compare it; this asserts the seed default instead.
    Prompting, not routing: localhost:3128 is the sole egress either way, no credential is involved,
    and INV-14 (which keys on commands, not hosts) is untouched — this is not a relaxation.
    """
    d = json.loads(TEMPLATE_SETTINGS.read_text())
    domains = d.get("sandbox", {}).get("network", {}).get("allowedDomains", [])
    assert "api.github.com" in domains, "seed lacks api.github.com — gh_read/pr-flow reads at risk"
    assert "github.com" in domains, "seed lacks github.com"
    allow = d.get("permissions", {}).get("allow", [])
    assert "WebFetch(domain:github.com)" in allow, "seed lacks WebFetch(domain:github.com)"


def test_seed_template_does_not_seed_write_access_to_other_repos():
    """Item 38, the deliberate allowWrite decision: a deployed VAULT has no business writing to the
    framework repo or the development store, so the template seeds NO allowWrite — each instance
    grants its own. (The dev machine's own vault carries those paths because it IS the dev machine;
    that instance divergence is legitimate for a SEED value, which is why item 38 is a seeded default
    plus a test, not a lockstep comparison.)
    """
    d = json.loads(TEMPLATE_SETTINGS.read_text())
    allow_write = d.get("sandbox", {}).get("filesystem", {}).get("allowWrite", [])
    assert allow_write == [], f"the template must not seed allowWrite, found: {allow_write}"
