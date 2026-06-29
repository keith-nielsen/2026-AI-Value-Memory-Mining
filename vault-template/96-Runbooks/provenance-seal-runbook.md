---
type: runbook
id: provenance-seal-runbook
title: Provenance seal — gold artifact (forensic, trustless)
trigger: "archive/seal an irreplaceable artifact so a third party can verify it without trusting us or any company"
applies-to: both
class: procedure
last-validated: 2026-06-17
---
# Runbook — Provenance Seal

## Purpose
Produce a tamper-evident, attribution-protected, independently-verifiable record of an
artifact (e.g. a co-design transcript): SHA-256/512 manifest + SSH signature +
OpenTimestamps/Bitcoin anchor + signed git tag. No trusted third party.

## Preconditions
- `[script]` OTS client on PATH at `~/.local/bin/ots` (pipx `opentimestamps-client`) — **not** the apt `ots`.
- `[gate]` signing key `~/.ssh/id_ed25519_signing` belongs to the operator; the agent MUST NOT sign or stamp as them.
- artifact lives in a git repo (private, for provenance).

## Steps
1. `[script]` Snapshot the artifact into the provenance repo's `transcripts/`. **If a prior sealed
   manifest exists, append a versioned `*.vX.Y.Z.*` copy — do NOT overwrite** (overwrite voids the
   prior Bitcoin attestation). `zstd -19` a sealed copy; verify it round-trips to the same `sha256`.
2. `[script]` `sha256sum` + `sha512sum` over raw + zstd → `SHA256SUMS.vX` / `SHA512SUMS.vX`.
3. `[gate]` Operator unlocks the key for the session: `sign-session` (dedicated 12h ssh-agent —
   gnome-keyring ignores `ssh-add -t`), then `source ~/.ssh/signing-agent.env`.
4. `[gate]` Operator signs: `ssh-keygen -Y sign -f ~/.ssh/id_ed25519_signing.pub -n file SHA256SUMS.vX`.
5. `[script]` `ots stamp SHA256SUMS.vX` (submits to calendars).
6. `[script]` commit the snapshot; `[gate]` operator `git tag -s archive-transcript-<date>-vX`.
7. `[script]` after ~1–6h, `ots upgrade transcripts/SHA256SUMS.vX.ots` (retry until "complete"),
   then commit + push the Bitcoin-anchored proof.

## Pitfalls
- Do **not** `sudo apt install ots` — wrong package. Use the pipx client at `~/.local/bin/ots`.
- gnome-keyring caches keys for the whole login session and ignores `ssh-add -t` → use `sign-session` for a real TTL.
- Overwriting an existing sealed manifest voids its confirmed Bitcoin attestation → always append a new snapshot.
- The agent MUST NOT sign/stamp/tag as the operator; steps 3–4 and 6 are the operator's `[gate]`.

## Verification
- `sha256sum -c SHA256SUMS.vX` — integrity.
- `ssh-keygen -Y verify -f allowed_signers -I <email> -n file -s SHA256SUMS.vX.sig < SHA256SUMS.vX` → `Good`.
- `ots info transcripts/SHA256SUMS.vX.ots` shows a `BitcoinBlockHeaderAttestation(<height>)`.
- `git tag -v archive-transcript-<date>-vX` → `Good`.

## Rollback
- Before the tag/push: delete the new `*.vX.*` files — the prior seal is untouched (that is *why* we append).
- After push: a bad snapshot is additive — supersede it with a corrected `*.vX+1.*` snapshot; never rewrite history.
