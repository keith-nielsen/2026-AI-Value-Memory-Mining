<!-- SPDX-License-Identifier: Apache-2.0 -->
## Context

The vault's safety invariants (INV-4, INV-5, INV-7) define what automated processes
must not do. The commit-gate hook enforces name conformance at commit time, but it
does not observe: (a) writes that happen outside the Git lifecycle, (b) unexpected
network connections from vault processes, or (c) reads of sensitive Treasury content
by processes that should not have access.

osquery (Kolide/Facebook, Apache-2.0) is a SQL-based OS instrumentation framework
that exposes filesystem, process, and network state as queryable tables. It runs as
a local daemon and is appropriate for single-host, privacy-preserving monitoring.

## Goals / Non-Goals

**Goals:**
- FIM on `40-Treasury/` and `99-Operations/` — detect writes by unexpected processes
- Egress monitoring — detect network connections from vault Python processes
- Local-only output (log file, no external endpoint)

**Non-Goals:**
- Real-time blocking (osquery observes; enforcement is by existing hooks)
- Cloud telemetry or any remote data transmission
- Monitoring non-vault areas of the filesystem

## Decisions

**osquery over inotify/kqueue directly.** osquery abstracts the OS-level FIM API
and provides a SQL query interface that non-systems engineers can read and audit.
The query files are human-readable and version-controlled in `99-Operations/`.

**Local log file, not a SIEM.** The vault is a single-person system; shipping
events to an external SIEM would introduce a data exfiltration risk that defeats
the privacy posture. Alert output is a local append-only log in `99-Operations/`.

**Deferred until OS ACL hardening.** Telemetry without enforcement is incomplete
observability. The OS-level write-protection of `99-Operations/` (deferred, §14.1)
should be implemented first so that FIM alerts have a meaningful enforcement backstop.

## Risks / Trade-offs

- osquery adds an optional runtime dependency (the vault's deterministic scripts
  remain dependency-free per INV-6; osquery is an operational tool, not a script dep).
- FIM query schedules must not fire so frequently as to become a performance concern
  on large vaults; schedule tuning is part of activation.
