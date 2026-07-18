#!/usr/bin/env python3
"""Ship-release driver — a guarded, re-entrant state machine for the tag -> Release ceremony.

Mechanizes CONTRIBUTING "Shipping a version" so the ceremony's hazards are guard clauses at
their point of action instead of recollections (the F10/F21 record in the live vault's
determinism-failure-modes Site): merge-ancestor proof before any tag exists (never
tag-before-merge), CHANGELOG-entry proof (a release without its entry shipped once), stale-tag
refusal that names the true cause and both commits (a guard once mis-reported "not merged"
when the cause was a leftover local tag), and a closing tag<->Release parity tally with its
denominator.

Deliberately NEVER executes an outward mutation. `git push` and `gh release create` are
ASK-gated by the INV-14 outbound guard, which text-matches the command the agent runs; a
wrapper that ran them internally would bypass that rail. So the driver proves every guard,
performs only the local reversible mutation (the annotated tag), then EMITS the next single
outward command verbatim and exits 2 (needs-input). The caller runs that one command through
the normal gated channel and re-invokes the driver, which verifies the mutation actually
landed (silent gh successes are not trusted) before advancing. Each invocation re-derives the
state from the world — it holds no state file and is safe to re-run at any point.

Network posture: this is a ceremony tool, not a deterministic fleet script — it legitimately
performs authenticated reads (`git fetch`/`ls-remote`, `gh release view/list`), so INV-6 is
not engaged (see the maintenance spec's Release-object requirement). All its own actions are
reads plus the local tag; everything outward is emitted, never run.

Usage:  tools/ship-release.py vX.Y.Z [--commit SHA] [--base BRANCH] [--title STR]
Exit:   0 ship complete, parity verified · 1 guard refused · 2 next gated command emitted ·
        3 blocked (bad invocation / not a repo / gh or remote unreachable).
"""
import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_NEEDS_INPUT = 2
EXIT_BLOCKED = 3

VERSION_RE = re.compile(r"^v\d+\.\d+\.\d+$")


def _die_blocked(msg):
    print(f"BLOCKED: {msg}")
    raise SystemExit(EXIT_BLOCKED)


def _refuse(msg):
    print(f"REFUSED: {msg}")
    raise SystemExit(EXIT_REFUSED)


def _emit_next(cmd):
    print("NEXT: run exactly this one command through the normal gated channel, then re-run")
    print("NEXT: the driver — it verifies the mutation landed before advancing.")
    print(f"NEXT: {cmd}")
    raise SystemExit(EXIT_NEEDS_INPUT)


def _run(args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def _git(root, *args):
    return _run(["git", "-C", str(root), *args])


def _semver_key(tag):
    return tuple(int(p) for p in tag[1:].split("."))


def changelog_section(root, version):
    """The `## [X.Y.Z]` section body from CHANGELOG.md, or None."""
    path = root / "CHANGELOG.md"
    if not path.is_file():
        _die_blocked(f"no CHANGELOG.md at {path}")
    lines = path.read_text().splitlines()
    bare = version[1:]
    out, capturing = [], False
    for line in lines:
        if line.startswith("## "):
            if capturing:
                break
            capturing = line.startswith(f"## [{bare}]")
        elif capturing:
            out.append(line)
    return "\n".join(out).strip() if capturing or out else None


def local_tag_commit(root, tag):
    r = _git(root, "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}^{{commit}}")
    return r.stdout.strip() or None


def remote_tag_commit(root, tag):
    """The commit the remote tag peels to (annotated or lightweight), or None."""
    r = _git(root, "ls-remote", "origin", f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}")
    if r.returncode != 0:
        _die_blocked(f"ls-remote origin failed: {r.stderr.strip()}")
    refs = {}
    for line in r.stdout.splitlines():
        sha, _, ref = line.partition("\t")
        refs[ref] = sha
    return refs.get(f"refs/tags/{tag}^{{}}") or refs.get(f"refs/tags/{tag}")


def remote_version_tags(root):
    r = _git(root, "ls-remote", "--refs", "origin", "refs/tags/v*")
    if r.returncode != 0:
        _die_blocked(f"ls-remote origin failed: {r.stderr.strip()}")
    tags = []
    for line in r.stdout.splitlines():
        name = line.partition("\t")[2].removeprefix("refs/tags/")
        if VERSION_RE.match(name):
            tags.append(name)
    return sorted(tags, key=_semver_key)


def gh_release(root, tag):
    """Release JSON for the tag, or None when the release does not exist.

    `isLatest` is deliberately NOT requested here: live gh exposes it on
    `release list` only — `release view --json` rejects the field (found by
    dogfooding the driver on its own first ship).
    """
    r = _run(["gh", "release", "view", tag, "--json", "tagName,isDraft"],
             cwd=str(root))
    if r.returncode == 0:
        return json.loads(r.stdout)
    if "release not found" in (r.stdout + r.stderr).lower():
        return None
    _die_blocked(f"gh release view {tag} failed: {r.stderr.strip()}")


def gh_release_list(root):
    """[{tagName, isLatest}] for every release — the only surface carrying isLatest."""
    r = _run(["gh", "release", "list", "--limit", "200",
              "--json", "tagName,isLatest"], cwd=str(root))
    if r.returncode != 0:
        _die_blocked(f"gh release list failed: {r.stderr.strip()}")
    return json.loads(r.stdout)


def main(argv):
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("version")
    ap.add_argument("--commit", help="release commit (default: tip of origin/<base>)")
    ap.add_argument("--base", default="main")
    ap.add_argument("--title", help="release title (default: the version)")
    ns = ap.parse_args(argv[1:])
    version = ns.version

    if not VERSION_RE.match(version):
        _die_blocked(f"'{version}' is not a vX.Y.Z version tag")
    if shutil.which("gh") is None:
        _die_blocked("gh CLI not found on PATH")
    top = _run(["git", "rev-parse", "--show-toplevel"])
    if top.returncode != 0:
        _die_blocked("not inside a git repository")
    root = pathlib.Path(top.stdout.strip())

    # Inbound refresh only — the remote's truth, read fresh every invocation.
    if _git(root, "fetch", "--quiet", "origin", ns.base).returncode != 0:
        _die_blocked(f"git fetch origin {ns.base} failed — remote unreachable?")
    origin_base = _git(root, "rev-parse", f"origin/{ns.base}").stdout.strip()
    if ns.commit:
        r = _git(root, "rev-parse", "--verify", "--quiet", f"{ns.commit}^{{commit}}")
        if r.returncode != 0:
            _die_blocked(f"--commit {ns.commit} does not resolve to a commit")
        target = r.stdout.strip()
    else:
        target = origin_base

    # Guard 1 (F10): the release content must already be merged. No tag exists before this proof.
    r = _git(root, "merge-base", "--is-ancestor", target, f"origin/{ns.base}")
    if r.returncode != 0:
        _refuse(f"[branch] target {target[:12]} is NOT an ancestor of origin/{ns.base} "
                f"({origin_base[:12]}) — the work is not merged. Never tag before merge; "
                f"merge first, then re-run.")
    print(f"guard [branch]: target {target[:12]} is an ancestor of "
          f"origin/{ns.base} ({origin_base[:12]})")

    # Guard 2 (F10 false-start 3): the CHANGELOG entry exists before anything ships.
    notes = changelog_section(root, version)
    if not notes:
        _refuse(f"[changelog] CHANGELOG.md has no '## [{version[1:]}]' section — "
                f"write the entry (and merge it) before shipping.")
    print(f"guard [changelog]: '## [{version[1:]}]' entry found "
          f"({len(notes.splitlines())} lines)")

    # Layer reads — one line per layer, each named (GitHub is a stack, not an oracle: F21).
    local = local_tag_commit(root, version)
    remote = remote_tag_commit(root, version)
    release = gh_release(root, version)
    rel_list = gh_release_list(root) if release else []
    latest_tag = next((x["tagName"] for x in rel_list if x.get("isLatest")), None)
    print(f"layer [local-tag]: {version} " + (f"at {local[:12]}" if local else "absent"))
    print(f"layer [remote-tag]: {version} " + (f"at {remote[:12]}" if remote else "absent"))
    print(f"layer [release-object]: {version} "
          + (f"exists (draft={release['isDraft']}, latest={latest_tag == version})"
             if release else "absent"))

    # Stale-tag refusals name the true cause and both commits (F10 false-start 7: a guard
    # once mis-reported a leftover tag as "not merged").
    if local and local != target:
        _refuse(f"[local-tag] {version} already exists at {local[:12]} but the target is "
                f"{target[:12]} — stale local tag, not a merge problem. Resolve it "
                f"deliberately (git tag -d {version}) and re-run.")
    if remote and remote != target:
        _refuse(f"[remote-tag] origin already has {version} at {remote[:12]} but the target "
                f"is {target[:12]} — the remote tag is on the wrong commit. This is the "
                f"tag-before-merge aftermath; fixing a published tag is a deliberate "
                f"human decision, not a driver action.")

    if local is None:
        # The one mutation the driver owns: local, reversible, behind both guards.
        r = _git(root, "tag", "-a", version, "-m", version, target)
        if r.returncode != 0:
            _die_blocked(f"git tag failed: {r.stderr.strip()}")
        created = local_tag_commit(root, version)
        if created != target:
            _refuse(f"[local-tag] post-create verification failed: tag peels to "
                    f"{(created or 'nothing')[:12]}, expected {target[:12]}")
        print(f"mutated [local-tag]: created annotated {version} at {target[:12]}, "
              f"verified by re-read")

    if remote is None:
        _emit_next(f"git push origin refs/tags/{version}")

    if release is None:
        notes_file = root / ".git" / f"ship-release-notes-{version}.md"
        notes_file.write_text(notes + "\n")
        print(f"notes [changelog]: release notes written to {notes_file}")
        title = ns.title or version
        _emit_next(f'gh release create {version} --verify-tag --latest '
                   f'-t "{title}" --notes-file {notes_file}')

    problems = []
    if release["isDraft"]:
        problems.append(f"release {version} is a DRAFT — publish it")
    all_tags = remote_version_tags(root)
    released = sorted({x["tagName"] for x in rel_list})
    if latest_tag != version and all_tags and all_tags[-1] == version:
        problems.append(f"release {version} is the newest version tag but is not marked "
                        f"Latest — the Releases surface tracks Release objects, not tags")
    missing = [t for t in all_tags if t not in released]
    extra = [t for t in released if t not in all_tags]
    for t in missing:
        print(f"parity-miss [release-object]: tag {t} has no Release")
    for t in extra:
        print(f"parity-miss [remote-tag]: release {t} has no version tag on origin")
    print(f"parity: {len(all_tags)} version tags on origin / {len(released)} releases — "
          f"{len(missing)} tags without a release, {len(extra)} releases without a tag")
    for p in problems:
        print(f"REFUSED: [release-object] {p}")
    return EXIT_REFUSED if (problems or missing or extra) else EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
