# SPDX-License-Identifier: Apache-2.0
"""The relay-conformance Stop hook (item 40): byte-checks a relayed next.sh line against the driver's
emission, blocks a mismatch AT MOST ONCE per emission, and fails open on everything else.

The hook is extracted from its literate note (INV-3) and run as a real subprocess, the way the
harness runs it — so its exit codes (0 pass / 2 block) are observed, not imported.
"""
import json
import os
import pathlib
import re
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
NOTE = REPO / "vault-template/99-Operations/scripts/relay-conformance-guard-script.md"


@pytest.fixture(scope="module")
def guard(tmp_path_factory):
    assert NOTE.exists(), f"{NOTE.relative_to(REPO)} is missing; the hook has no source of truth"
    m = re.search(r"^## Implementation\s*\n```python\n(.*?)^```",
                  NOTE.read_text(encoding="utf-8"), re.S | re.M)
    assert m, "no python implementation block in the relay-conformance note"
    p = tmp_path_factory.mktemp("relayguard") / "relay-conformance-guard.py"
    p.write_text(m.group(1), encoding="utf-8")
    return p


def _repo(tmp_path, canonical):
    """A repo dir carrying the driver's canonical relay-line sidecar."""
    d = tmp_path / "repo"
    (d / ".git" / "pr-flow").mkdir(parents=True)
    (d / ".git" / "pr-flow" / "relay-line.txt").write_text(canonical + "\n", encoding="utf-8")
    return d


def _msg(line):
    """An assistant message that relays `line` inside a START COPY/END COPY block."""
    return f"Here you go:\n\nSTART COPY\n```bash\n{line}\n```\nEND COPY\n\nRun it when ready."


def run(guard, message, cwd):
    r = subprocess.run([sys.executable, str(guard)],
                       input=json.dumps({"last_assistant_message": message, "cwd": str(cwd),
                                         "hook_event_name": "Stop"}),
                       capture_output=True, text=True, env=dict(os.environ))
    return r.returncode, r.stderr


CANON = "bash /repo/.git/pr-flow/next.sh   # body step:pr -> new PR"


def test_a_verbatim_relay_passes(guard, tmp_path):
    d = _repo(tmp_path, CANON)
    line = f"bash {d}/.git/pr-flow/next.sh   # body step:pr -> new PR"
    # sidecar must match the relayed line byte-for-byte
    (d / ".git" / "pr-flow" / "relay-line.txt").write_text(line + "\n", encoding="utf-8")
    code, _ = run(guard, _msg(line), d)
    assert code == 0


def test_a_drifted_relay_is_blocked(guard, tmp_path):
    d = _repo(tmp_path, CANON)
    canon = f"bash {d}/.git/pr-flow/next.sh   # body step:pr -> new PR"
    (d / ".git" / "pr-flow" / "relay-line.txt").write_text(canon + "\n", encoding="utf-8")
    drifted = f"bash {d}/.git/pr-flow/next.sh"  # tag dropped
    code, err = run(guard, _msg(drifted), d)
    assert code == 2, "a drifted relay was not blocked"
    assert canon in err, "the block message must name the correct line"


def test_block_once_then_falls_through(guard, tmp_path):
    """THE LOOP GUARD: a second identical mismatch for the same emission does NOT block again."""
    d = _repo(tmp_path, CANON)
    canon = f"bash {d}/.git/pr-flow/next.sh   # body step:pr -> new PR"
    (d / ".git" / "pr-flow" / "relay-line.txt").write_text(canon + "\n", encoding="utf-8")
    drifted = f"bash {d}/.git/pr-flow/next.sh"

    code1, _ = run(guard, _msg(drifted), d)
    assert code1 == 2, "first mismatch should block"
    code2, err2 = run(guard, _msg(drifted), d)
    assert code2 == 0, "second identical mismatch must NOT block again (loop guard)"
    assert "already flagged" in err2 or "not blocking again" in err2


def test_a_new_emission_re_arms_one_block(guard, tmp_path):
    """A new emitted step (new sidecar) re-arms exactly one block."""
    d = _repo(tmp_path, CANON)
    side = d / ".git" / "pr-flow" / "relay-line.txt"
    canon1 = f"bash {d}/.git/pr-flow/next.sh   # body step:pr -> new PR"
    side.write_text(canon1 + "\n", encoding="utf-8")
    drift1 = f"bash {d}/.git/pr-flow/next.sh"
    assert run(guard, _msg(drift1), d)[0] == 2
    assert run(guard, _msg(drift1), d)[0] == 0  # blocked once

    # new emission: different sidecar content
    canon2 = f"bash {d}/.git/pr-flow/next.sh   # body step:merge -> PR #9"
    side.write_text(canon2 + "\n", encoding="utf-8")
    drift2 = f"bash {d}/.git/pr-flow/next.sh --wrong"
    assert run(guard, _msg(drift2), d)[0] == 2, "a new emission should re-arm one block"


def test_a_correct_relay_clears_the_marker(guard, tmp_path):
    """After a block, relaying correctly clears the marker so a later drift re-arms."""
    d = _repo(tmp_path, CANON)
    side = d / ".git" / "pr-flow" / "relay-line.txt"
    canon = f"bash {d}/.git/pr-flow/next.sh   # body step:pr -> new PR"
    side.write_text(canon + "\n", encoding="utf-8")
    drift = f"bash {d}/.git/pr-flow/next.sh"
    assert run(guard, _msg(drift), d)[0] == 2          # block
    assert run(guard, _msg(canon), d)[0] == 0          # correct relay clears the marker
    assert run(guard, _msg(drift), d)[0] == 2          # drift blocks again (re-armed)


def test_no_relay_block_is_ignored(guard, tmp_path):
    d = _repo(tmp_path, CANON)
    code, _ = run(guard, "Just a status update mentioning bash /x/.git/pr-flow/next.sh in prose.", d)
    assert code == 0, "a line outside a START COPY block is not a relay"


def test_missing_sidecar_fails_open(guard, tmp_path):
    d = tmp_path / "norepo"
    (d / ".git").mkdir(parents=True)
    line = f"bash {d}/.git/pr-flow/next.sh   # body step:pr -> new PR"
    code, _ = run(guard, _msg(line), d)
    assert code == 0, "no sidecar must fail open"


def test_malformed_input_fails_open(guard):
    r = subprocess.run([sys.executable, str(guard)], input="not json at all",
                       capture_output=True, text=True, env=dict(os.environ))
    assert r.returncode == 0, "malformed input must fail open"


def test_driver_writes_the_sidecar_byte_identical_to_the_block(tmp_path):
    """The sidecar the driver writes equals the command inside the copy-whole block (item-40 contract)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("prf", REPO / "tools" / "pr-flow.py")
    prf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prf)
    d = tmp_path / "repo"
    (d / ".git").mkdir(parents=True)
    route = prf.Route()
    prf.emit(route, "merge", "cd /x && gh api -X PUT /repos/o/r/pulls/1/merge -f sha=abc",
             prf.OPERATOR, prf.OPERATOR, prf.CONSENT_ACT, "why", root=str(d), branch="feat/x")
    sidecar = (d / ".git" / "pr-flow" / "relay-line.txt").read_text().strip()
    expected = f"bash {d / '.git' / 'pr-flow' / 'next.sh'}{prf.plan_history_suffix('merge')}"
    assert sidecar == expected, f"sidecar {sidecar!r} != emitted line {expected!r}"


def test_an_indented_relay_is_caught(guard, tmp_path):
    """F43 historical-regression finding: an INDENTED paste is mangled, so it must read as drift.
    The first cut required `bash` at column 0 and silently passed an indented relay."""
    d = _repo(tmp_path, CANON)
    canon = f"bash {d}/.git/pr-flow/next.sh   # body step:pr -> new PR"
    (d / ".git" / "pr-flow" / "relay-line.txt").write_text(canon + "\n", encoding="utf-8")
    indented = f"  {canon}"  # same command, indented — mangles the paste
    code, _ = run(guard, _msg(indented), d)
    assert code == 2, "an indented relay must be caught as drift"
