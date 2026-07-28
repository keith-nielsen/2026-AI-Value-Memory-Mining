#!/usr/bin/env bash
# INV-6 dynamic half — run the fleet suite with no network at all, and prove the isolation
# is real before trusting the result.
#
# The whole value of this job is the CONTROL. A suite that passes inside a namespace which
# silently failed to isolate proves nothing, and would print green forever — the F20 /
# control-validity failure that this operation has now recorded four times. So: the network
# must be shown reachable OUTSIDE and unreachable INSIDE, in the same run, before any pass
# is believed. If isolation cannot be established, this exits non-zero. Fail closed: an
# unisolated run is not a weaker result, it is no result.
#
# Two namespace modes, because util-linux availability varies by runner image:
#   --map-current-user : preferred. Keeps our uid, so file-permission semantics are intact.
#   -r                 : fallback. Maps us to root IN THE NAMESPACE, and root bypasses
#                        permission bits — which breaks exactly one test that deliberately
#                        asserts EACCES (`test_non_erofs_oserror_is_not_swallowed`). That
#                        test is about errno propagation, not about INV-6, so it is
#                        deselected in fallback mode ONLY, and the mode is printed.
set -uo pipefail

# Exit codes follow the fleet contract, and the distinction is the point: an INVALID
# INSTRUMENT and a REAL VIOLATION must never look alike to CI. The first run of this job
# returned 1 for "no namespace available", which is indistinguishable from "a fleet script
# called the network" — the exact conflation this operation keeps getting burned by.
EXIT_OK=0
EXIT_VIOLATION=1     # the suite failed with no network — a genuine INV-6 signal
EXIT_BLOCKED=3       # the instrument could not be established — NO verdict about INV-6

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO" || exit 2
PROBE_URL="https://api.github.com/rate_limit"

echo "== control 1: the network must be reachable OUTSIDE the namespace =="
if ! curl -sS -o /dev/null --max-time 25 "$PROBE_URL"; then
  echo "BLOCKED: no network on this runner, so 'blocked inside' would be meaningless." >&2
  echo "  This is an INVALID instrument, not a passing test." >&2
  exit "$EXIT_BLOCKED"
fi
echo "  ok: reachable outside"

# Capture WHY, never swallow it. The first CI failure printed only "namespace mode: none",
# which required pulling the job log and still did not say why — a diagnostic gap that cost
# a round trip. The reason is now printed at the point of failure.
NS_ERR_A="" NS_ERR_B="" MODE=""
# Deliberately NOT `MODE="$(pick_mode)"`: command substitution runs the function in a
# SUBSHELL, so the NS_ERR_* assignments would be discarded and the diagnostic would print
# "<no message>" — which is precisely the failure this block exists to prevent. Caught by
# exercising the branch with a stubbed `unshare` rather than assuming it worked.
pick_mode() {
  if NS_ERR_A="$(unshare --map-current-user -n true 2>&1)"; then MODE="map-current-user"; return; fi
  if NS_ERR_B="$(unshare -rn true 2>&1)"; then MODE="root-mapped"; return; fi
  MODE="none"
}
pick_mode
echo "== namespace mode: $MODE =="
if [ "$MODE" = "none" ]; then
  {
    echo "BLOCKED: no unprivileged network namespace available on this runner."
    echo "  Cannot isolate, therefore cannot claim INV-6 behaviour. Fail closed."
    echo
    echo "  unshare --map-current-user -n : ${NS_ERR_A:-<no message>}"
    echo "  unshare -rn                   : ${NS_ERR_B:-<no message>}"
    echo
    echo "  Kernel policy at the time of failure:"
    for k in kernel.apparmor_restrict_unprivileged_userns kernel.unprivileged_userns_clone \
             user.max_user_namespaces; do
      echo "    $(sysctl -n "$k" 2>/dev/null | sed "s|^|$k = |" || echo "$k = <absent>")"
    done
    echo
    echo "  Ubuntu 24.04+ ships kernel.apparmor_restrict_unprivileged_userns=1, which blocks this."
    echo "  The CI job sets it to 0 for the runner; if you are seeing this, that step did not take."
  } >&2
  exit "$EXIT_BLOCKED"
fi

case "$MODE" in
  map-current-user) NS=(unshare --map-current-user -n) ;;
  root-mapped)      NS=(unshare -rn) ;;
esac

echo "== control 2: the network must be UNREACHABLE inside the namespace =="
if "${NS[@]}" curl -s -o /dev/null --max-time 10 "$PROBE_URL"; then
  echo "BLOCKED: the namespace did not isolate the network — a pass here would be false assurance." >&2
  exit "$EXIT_BLOCKED"
fi
echo "  ok: blocked inside"

echo "== fleet suite, offline =="
if [ "$MODE" = "root-mapped" ]; then
  echo "  (fallback mode: deselecting test_non_erofs_oserror_is_not_swallowed — it asserts EACCES,"
  echo "   which root cannot experience. Not an INV-6 test.)"
  "${NS[@]}" python3 -m pytest tests/test_fleet.py -q \
      --deselect tests/test_fleet.py::test_non_erofs_oserror_is_not_swallowed
else
  "${NS[@]}" python3 -m pytest tests/test_fleet.py -q
fi
rc=$?

echo
if [ "$rc" -eq 0 ]; then
  echo "INV-6 dynamic: fleet suite completed with NO network available (mode: $MODE)."
  echo "BOUND: this proves the paths the suite EXERCISES make no network call. It does not"
  echo "  prove the fleet is offline on unexercised paths — notably the two INV-14 guards,"
  echo "  which currently have no tests. Coverage is the limit, and it is stated, not hidden."
else
  echo "INV-6 dynamic: the fleet suite FAILED with no network available." >&2
  echo "  This is exit $EXIT_VIOLATION — a genuine INV-6 signal, NOT an instrument problem" >&2
  echo "  (those exit $EXIT_BLOCKED). Before concluding a network cause, run the same suite in a" >&2
  echo "  plain environment: if it also fails there, the cause is not the missing network." >&2
  rc="$EXIT_VIOLATION"
fi
exit "$rc"
