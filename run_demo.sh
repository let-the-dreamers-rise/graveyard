#!/usr/bin/env bash
# GRAVEYARD — one-command demo for video recording (SIFT / Linux / macOS)
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

EXPORTS="${EXPORTS:-examples/sample_exports}"
V1="${V1:-examples/findings_draft_v1_reject.json}"
V2="${V2:-examples/findings_draft_v2_pass.json}"
REPORT="${REPORT:-reports/report.md}"
PAUSE="${PAUSE:-4}"

pause_step() {
  echo ""
  echo ">>> Press Enter to continue (or wait ${PAUSE}s)..."
  read -r -t "$PAUSE" || true
  echo ""
}

echo "=============================================="
echo " GRAVEYARD Demo — ghost correlate + verifier"
echo " Repo: $REPO_DIR"
echo "=============================================="
pause_step

echo "=== Step 1/4: graveyard_correlate ==="
python3 graveyard_correlate.py --exports "$EXPORTS"
pause_step

echo "=== Step 2/4: verify_findings v1 (expect REJECT) ==="
set +e
python3 verify_findings.py "$V1" --exports "$EXPORTS" --json-out
V1_EXIT=$?
set -e
echo "Exit code: $V1_EXIT (expect 1)"
pause_step

echo "=== Step 3/4: verify_findings v2 (expect PASS) ==="
python3 verify_findings.py "$V2" --exports "$EXPORTS" --report "$REPORT"
echo "Exit code: $? (expect 0)"
pause_step

echo "=== Step 4/4: verified report ==="
echo "--- $REPORT ---"
cat "$REPORT"
echo ""
echo "=============================================="
echo " Demo complete. Audit log: docs/execution_logs/"
echo "=============================================="
