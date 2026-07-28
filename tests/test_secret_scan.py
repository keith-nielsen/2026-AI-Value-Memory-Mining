"""Behaviour tests for the INV-7 credential scanner and its commit-gate integration.

Every test drives the *deployed* script as a subprocess through the shared `fleet` fixture —
the runtime it actually ships in — so these prove behaviour rather than re-implementing the
regexes. The synthetic tokens below are format-valid and value-worthless by construction
(runs of a single character); they exist to make the gate fail, which is the only way to know
it can.
"""
import pytest

EXIT_OK, EXIT_FOUND, EXIT_SELFTEST = 0, 1, 3

# Format-valid, value-worthless. Built rather than literal so no real-looking token is ever
# committed to this repo — the scanner would (correctly) block this very file otherwise.
GITHUB_PAT = "ghp_" + "A" * 36
NPM_TOKEN = "npm_" + "B" * 36
AWS_KEY = "AKIA" + "ABCDEFGHIJKLMNOP"
# Concatenated for the same reason: this module is scanned by the CI job and by the commit
# gate, so a literal header would make the scanner flag its own test suite in perpetuity.
PRIVATE_KEY = "-----BEGIN " + "OPENSSH " + "PRIVATE KEY" + "-----"


def test_selftest_passes_on_a_healthy_instrument(fleet):
    # The control for every other test in this file. If the patterns cannot be shown to
    # fire, a "clean" result from any other test means nothing.
    r = fleet.run("vault_secrets.py", "--selftest")
    assert r.returncode == EXIT_OK, r.stdout + r.stderr


def test_commit_gate_blocks_a_staged_credential(fleet):
    fleet.write("20-Claims/some-conforming-note.md", f"token: {GITHUB_PAT}\n")
    fleet.git("add", "20-Claims/some-conforming-note.md")
    r = fleet.git("commit", "-m", "stage a credential")   # gate must fire
    out = r.stdout + r.stderr
    assert r.returncode != 0, out
    assert "BLOCKED" in out, out
    assert "INV-7" in out, out


def test_gate_message_redacts_the_secret(fleet):
    # A scanner that echoes what it found writes the secret to the terminal, the shell
    # history and possibly a log — violating INV-7 while enforcing it.
    fleet.write("20-Claims/another-conforming-note.md", f"key = {AWS_KEY}\n")
    fleet.git("add", "20-Claims/another-conforming-note.md")
    r = fleet.git("commit", "-m", "stage an aws key")
    out = r.stdout + r.stderr
    assert r.returncode != 0, out
    assert AWS_KEY not in out, "the full secret leaked into the gate output"
    assert "AKIA..." in out, out


def test_gate_passes_clean_content(fleet):
    fleet.write("20-Claims/a-perfectly-clean-note.md", "# notes\nnothing secret here\n")
    fleet.git("add", "20-Claims/a-perfectly-clean-note.md")
    r = fleet.git("commit", "-m", "clean content")
    assert r.returncode == 0, r.stdout + r.stderr


def test_prose_about_secrets_does_not_trip_the_gate(fleet):
    # RC-E: over-denial is camouflage. This vault's own audit notes discuss tokens
    # constantly; a gate that fires on them would be routed around within a week.
    fleet.write(
        "30-Sites/some-audit-site/some-audit-note.md",
        "The guard is blind to `gh api`. Do not export GH_TOKEN or a PyPI token here.\n"
        'Patterns like password = "..." are advisory only.\n',
    )
    fleet.git("add", "-A")
    r = fleet.git("commit", "-m", "prose about credentials")
    assert r.returncode == 0, r.stdout + r.stderr


def test_credentials_are_not_grandfathered(fleet):
    # Deliberate asymmetry with INV-11: a pre-existing bad NAME is grandfathered
    # (--diff-filter=AR), a pre-existing credential is not (--diff-filter=ACM).
    fleet.write("20-Claims/a-pre-existing-note.md", "clean at first\n")
    fleet.setup_commit("land the file with the gate bypassed")
    (fleet.vault / "20-Claims" / "a-pre-existing-note.md").write_text(f"now: {NPM_TOKEN}\n")
    fleet.git("add", "20-Claims/a-pre-existing-note.md")
    r = fleet.git("commit", "-m", "modify a pre-existing file")   # M, not A/R
    out = r.stdout + r.stderr
    assert r.returncode != 0, out
    assert "INV-7" in out, out


def test_gate_covers_non_markdown_files(fleet):
    # The naming half only looks at *.md. A secret in a .json or .env counts just as much.
    fleet.write("20-Claims/some-staged-config.json", '{"token": "%s"}\n' % GITHUB_PAT)
    fleet.git("add", "20-Claims/some-staged-config.json")
    r = fleet.git("commit", "-m", "stage a json config")
    assert r.returncode != 0, r.stdout + r.stderr


@pytest.mark.parametrize("payload,label", [
    (GITHUB_PAT, "github-pat-classic"),
    (NPM_TOKEN, "npm-token"),
    (AWS_KEY, "aws-access-key"),
    (PRIVATE_KEY, "private-key-block"),
])
def test_path_scan_detects_each_high_format(fleet, payload, label):
    fleet.write("20-Claims/a-scanned-sample-note.md", f"{payload}\n")
    r = fleet.run("vault_secrets.py", str(fleet.vault / "20-Claims"))
    assert r.returncode == EXIT_FOUND, r.stdout + r.stderr
    assert label in r.stdout, r.stdout


def test_history_scan_finds_an_unreachable_blob(fleet):
    # The property that separates a historical scan from `rev-list`: a secret committed and
    # then discarded by `reset --hard` survives in the object DB, unreachable but present.
    fleet.write("20-Claims/a-discarded-secret-note.md", f"{GITHUB_PAT}\n")
    fleet.setup_commit("commit a secret")
    fleet.git("reset", "--hard", "HEAD~1")
    r = fleet.run("vault_secrets.py", "--history", str(fleet.vault))
    assert r.returncode == EXIT_FOUND, r.stdout + r.stderr
    assert "unreachable blob" in r.stdout, r.stdout


def test_advisory_tier_never_gates(fleet):
    # `password = "..."` is reported by the standalone tool and ignored by the hook.
    fleet.write("20-Claims/an-advisory-only-note.md", 'password = "hunter2000"\n')
    r = fleet.run("vault_secrets.py", str(fleet.vault / "20-Claims"))
    assert r.returncode == EXIT_OK, r.stdout + r.stderr
    assert "ADVISORY" in r.stdout, r.stdout

    fleet.git("add", "20-Claims/an-advisory-only-note.md")
    c = fleet.git("commit", "-m", "advisory-tier content")
    assert c.returncode == 0, c.stdout + c.stderr
