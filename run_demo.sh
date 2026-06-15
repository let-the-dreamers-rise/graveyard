#!/usr/bin/env bash
# GRAVEYARD — one-command demo for video recording (SIFT / Linux / macOS)
# Uses deterministic agent_loop (engine → verify → auto-correct → verify)
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

EXPORTS="${EXPORTS:-examples/sample_exports}"
TIMELINE="${TIMELINE:-examples/disk_timeline_sample.json}"
PAUSE="${PAUSE:-4}"

pause_step() {
  echo ""
  echo ">>> Press Enter to continue (or wait ${PAUSE}s)..."
  read -r -t "$PAUSE" || true
  echo ""
}

echo "=============================================="
echo " GRAVEYARD Demo — unified engine + agent loop"
echo " Repo: $REPO_DIR"
echo "=============================================="
pause_step

echo "=== Step 1/3: graveyard_engine (scored report) ==="
ENGINE_ARGS=(--exports "$EXPORTS")
if [[ -f "$TIMELINE" ]]; then
  ENGINE_ARGS+=(--timeline "$TIMELINE" --output analysis/graveyard_engine_report.json)
else
  ENGINE_ARGS+=(--output analysis/graveyard_engine_report.json)
fi
python3 graveyard_engine.py "${ENGINE_ARGS[@]}"
pause_step

echo "=== Step 2/3: agent_loop (deterministic self-correction, no LLM) ==="
bash scripts/agent_loop.sh "$EXPORTS" "$TIMELINE"
AGENT_EXIT=$?
pause_step

echo "=== Step 3/3: latest verified report ==="
LATEST_REPORT="$(ls -t reports/report_*.md 2>/dev/null | head -1 || true)"
if [[ -n "$LATEST_REPORT" && -f "$LATEST_REPORT" ]]; then
  echo "--- $LATEST_REPORT ---"
  cat "$LATEST_REPORT"
else
  echo "(no timestamped report — check reports/report.md)"
  [[ -f reports/report.md ]] && cat reports/report.md
fi

echo ""
echo "=============================================="
echo " Demo complete. Agent loop exit: $AGENT_EXIT"
echo " Audit log: docs/execution_logs/"
echo "=============================================="
exit "$AGENT_EXIT"
