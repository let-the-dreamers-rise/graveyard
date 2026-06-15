#!/usr/bin/env bash
# GRAVEYARD spoliation test runner (SIFT/Linux) — PASS/FAIL summary for demo video
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

echo "=== GRAVEYARD Spoliation Tests ==="
echo "Repo: $REPO_DIR"
echo ""

TMPLOG="$(mktemp)"
set +e
if command -v pytest >/dev/null 2>&1; then
  python3 -m pytest tests/test_spoliation.py -v --tb=short 2>&1 | tee "$TMPLOG"
  EXIT=$?
else
  python3 tests/test_spoliation.py 2>&1 | tee "$TMPLOG"
  EXIT=$?
fi
set -e

PASSED=$(grep -cE "^\s*(ok|PASS|PASSED)" "$TMPLOG" 2>/dev/null || true)
FAILED=$(grep -cE "^\s*(FAIL|FAILED|ERROR)" "$TMPLOG" 2>/dev/null || true)
# unittest reports "Ran N tests"
RAN=$(grep -oE "Ran [0-9]+ tests" "$TMPLOG" | tail -1 || echo "Ran ? tests")

rm -f "$TMPLOG"

echo ""
echo "=============================================="
if [[ "$EXIT" -eq 0 ]]; then
  echo " RESULT: PASS — spoliation suite ($RAN)"
  echo " Tests document: evidence blocking, export traversal,"
  echo " attribution guard, fake citations, confidence guard,"
  echo " verifier read-only on exports."
else
  echo " RESULT: FAIL — spoliation suite ($RAN)"
  echo " Re-run: python3 tests/test_spoliation.py -v"
fi
echo "=============================================="
exit "$EXIT"
