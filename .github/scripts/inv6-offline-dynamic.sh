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

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO" || exit 2
PROBE_URL="https://api.github.com/rate_limit"

echo "== control 1: the network must be reachable OUTSIDE the namespace =="
if ! curl -sS -o /dev/null --max-time 25 "$PROBE_URL"; then
  echo "BLOCKED: no network on this runner, so 'blocked inside' would be meaningless." >&2
  echo "  This is an INVALID instrument, not a passing test." >&2
  exit 1
fi
echo "  ok: reachable outside"

pick_mode() {
  if unshare --map-current-user -n true 2>/dev/null; then echo "map-current-user"; return; fi
  if unshare -rn true 2>/dev/null; then echo "root-mapped"; return; fi
  echo "none"
}
MODE="$(pick_mode)"
echo "== namespace mode: $MODE =="
if [ "$MODE" = "none" ]; then
  echo "BLOCKED: no unprivileged network namespace available on this runner." >&2
  echo "  Cannot isolate, therefore cannot claim INV-6 behaviour. Fail closed." >&2
  exit 1
fi

case "$MODE" in
  map-current-user) NS=(unshare --map-current-user -n) ;;
  root-mapped)      NS=(unshare -rn) ;;
esac

echo "== control 2: the network must be UNREACHABLE inside the namespace =="
if "${NS[@]}" curl -s -o /dev/null --max-time 10 "$PROBE_URL"; then
  echo "BLOCKED: the namespace did not isolate the network — a pass here would be false assurance." >&2
  exit 1
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
  echo "INV-6 dynamic: FAILED with no network available — investigate before assuming a network cause;"
  echo "  a plain-environment run of the same suite is the discriminating comparison." >&2
fi
exit "$rc"
