"""Pytest harness for the Layer-0 script fleet.

Each test gets a throwaway `HOME` + vault rendered from `vault-template/`, exactly the
way `.github/scripts/validate-scripts.sh` builds its sandbox: bootstrap `vault-render.py`
from its own literate note, render the whole fleet into `$HOME/bin`, deploy the git hooks
into the vault, instantiate the private `config.env` from the example, and `git init` with
the naming gate active. Scripts are then exercised as real subprocesses — the runtime the
fleet actually ships in — so the tests prove behaviour, not a re-implementation of it.
"""

import dataclasses
import os
import re
import shutil
import subprocess
import sys
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = REPO / "vault-template"
PY = sys.executable  # the interpreter running pytest — has python-frontmatter (requirements.txt)


@dataclasses.dataclass
class Fleet:
    """A rendered fleet over an isolated HOME + vault; the handle every test drives."""

    vault: pathlib.Path
    home: pathlib.Path

    def env(self, vault_root=True):
        e = dict(os.environ)
        e["HOME"] = str(self.home)
        e.pop("VAULT_ROOT", None)
        if vault_root:
            e["VAULT_ROOT"] = str(self.vault)
        return e

    def run(self, script, *args, vault_root=True, cwd=None):
        """Invoke a deployed script (`vault-*.py` via PY, `*.sh` via its shebang)."""
        exe = self.home / "bin" / script
        cmd = ([PY, str(exe)] if script.endswith(".py") else [str(exe)])
        cmd += [str(a) for a in args]
        return subprocess.run(cmd, cwd=str(cwd or self.vault), env=self.env(vault_root),
                              capture_output=True, text=True)

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.vault), *args],
                              capture_output=True, text=True, env=self.env())

    def setup_commit(self, msg="setup"):
        """Stage + commit test scaffolding without the naming gate (mirrors the fixture's
        own `--no-verify` init); the gate is exercised by the scripts' own commits."""
        self.git("add", "-A")
        self.git("commit", "-qm", msg, "--no-verify")

    def write(self, rel, text):
        p = self.vault / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def read(self, rel):
        return (self.vault / rel).read_text()

    def exists(self, rel):
        return (self.vault / rel).exists()

    def head_message(self):
        return self.git("log", "-1", "--format=%s").stdout.strip()

    def head_files(self):
        r = self.git("show", "--name-only", "--format=", "HEAD")
        return [ln for ln in r.stdout.splitlines() if ln.strip()]

    def commit_count(self):
        return int(self.git("rev-list", "--count", "HEAD").stdout.strip() or 0)


def _render_fleet(source_vault, home):
    """Bootstrap the renderer from its source note, then render every script + hook.

    Mirrors validate-scripts.sh: a meta-script note is Markdown, so its code fence is
    extracted rather than executed. Run with cwd == the vault so the vault-relative hook
    targets (`99-Operations/hooks/pre-commit`, …) land inside the vault.
    """
    import frontmatter  # same dependency the fleet declares

    bindir = home / "bin"
    bindir.mkdir(parents=True, exist_ok=True)
    note = source_vault / "99-Operations" / "scripts" / "render-reconcile-script.md"
    code = re.search(r"^```python\n(.*?)^```", frontmatter.load(note).content,
                     re.S | re.M).group(1)
    render = bindir / "vault-render.py"
    render.write_text(code)
    render.chmod(0o755)
    env = {**os.environ, "HOME": str(home), "VAULT_ROOT": str(source_vault)}
    subprocess.run([PY, str(render), "render"], cwd=str(source_vault), env=env,
                   check=True, capture_output=True, text=True)
    # emit 99-Operations/schemas/naming-rules.json (the JSON mirror the hook/linter read)
    subprocess.run([PY, str(bindir / "vault_naming.py")], cwd=str(source_vault), env=env,
                   check=True, capture_output=True, text=True)


@pytest.fixture
def fleet(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    vault = tmp_path / "vault"
    shutil.copytree(TEMPLATE, vault)

    # instantiate the private config from the example and point it at the sandbox vault
    example = vault / "99-Operations" / "config.env.example"
    cfg = vault / "99-Operations" / "config.env"
    cfg.write_text(re.sub(r"(?m)^export VAULT_ROOT=.*$",
                          f'export VAULT_ROOT="{vault}"', example.read_text()))

    _render_fleet(vault, home)

    f = Fleet(vault=vault, home=home)
    f.git("init", "-q", "-b", "main")
    f.git("config", "user.name", "ci")
    f.git("config", "user.email", "ci@ci")
    f.git("config", "core.hooksPath", "99-Operations/hooks")
    f.git("add", "-A")
    f.git("commit", "-qm", "init", "--no-verify")
    return f
