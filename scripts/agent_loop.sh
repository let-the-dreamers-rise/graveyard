#!/usr/bin/env bash
# GRAVEYARD — deterministic autonomous self-correction loop (no LLM)
# correlate → draft → verify → auto-correct from engine facts → verify again
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPORTS="${1:-examples/sample_exports}"
TIMELINE="${2:-}"
CASE_DIR="${3:-$REPO_DIR}"
TS="$(date +%Y%m%d_%H%M%S)"

cd "$CASE_DIR"
mkdir -p analysis reports docs/execution_logs

echo "=== GRAVEYARD Agent Loop (deterministic self-correction) ==="
echo "Exports: $EXPORTS"
echo "Case:    $CASE_DIR"
echo ""

# Step 1: Unified engine
echo "[1/5] graveyard_engine"
ENGINE_ARGS=(--exports "$EXPORTS" --output "analysis/graveyard_engine_${TS}.json")
if [[ -n "$TIMELINE" && -f "$TIMELINE" ]]; then
  ENGINE_ARGS+=(--timeline "$TIMELINE")
fi
python3 "$REPO_DIR/graveyard_engine.py" "${ENGINE_ARGS[@]}"

# Step 2: Draft findings with intentional bad finding for demo
echo "[2/5] draft findings (with demo attribution violation)"
python3 "$REPO_DIR/scripts/auto_correct_findings.py" \
  --exports "$EXPORTS" \
  --engine-report "analysis/graveyard_engine_${TS}.json" \
  --output "findings_draft_v1_${TS}.json" \
  --inject-bad

# Step 3: Verify v1 — expect REJECT
echo "[3/5] verify v1 (expect REJECT)"
set +e
python3 "$REPO_DIR/verify_findings.py" "findings_draft_v1_${TS}.json" \
  --exports "$EXPORTS" \
  --audit-log "docs/execution_logs/agent_loop_${TS}.jsonl" \
  --json-out 2>&1 | tee "docs/execution_logs/agent_loop_v1_${TS}.txt"
V1_EXIT=$?
set -e
echo "v1 exit code: $V1_EXIT (expect 1)"

if [[ "$V1_EXIT" -eq 0 ]]; then
  echo "WARNING: v1 passed unexpectedly — skipping auto-correction demo branch"
  cp "findings_draft_v1_${TS}.json" "findings_draft_corrected_${TS}.json"
else
  # Step 4: Deterministic auto-correction from engine facts only
  echo "[4/5] auto_correct_findings (engine facts only, no LLM)"
  python3 "$REPO_DIR/scripts/auto_correct_findings.py" \
    --exports "$EXPORTS" \
    --engine-report "analysis/graveyard_engine_${TS}.json" \
    --output "findings_draft_corrected_${TS}.json"
fi

# Step 5: Verify corrected — expect PASS
echo "[5/5] verify corrected (expect PASS)"
python3 "$REPO_DIR/verify_findings.py" "findings_draft_corrected_${TS}.json" \
  --exports "$EXPORTS" \
  --report "reports/report_${TS}.md" \
  --audit-log "docs/execution_logs/agent_loop_${TS}.jsonl"
V2_EXIT=$?

echo ""
echo "=== Agent Loop Complete ==="
echo "  Engine report:     analysis/graveyard_engine_${TS}.json"
echo "  v1 (bad):          findings_draft_v1_${TS}.json  exit=$V1_EXIT"
echo "  Corrected:         findings_draft_corrected_${TS}.json  exit=$V2_EXIT"
echo "  Report (if PASS):  reports/report_${TS}.md"
echo "  Audit log:         docs/execution_logs/agent_loop_${TS}.jsonl"

if [[ "$V1_EXIT" -ne 0 && "$V2_EXIT" -eq 0 ]]; then
  echo ""
  echo "RESULT: PASS — deterministic self-correction demonstrated"
  exit 0
elif [[ "$V2_EXIT" -eq 0 ]]; then
  echo "RESULT: PASS — findings verified"
  exit 0
else
  echo "RESULT: FAIL — corrected findings still rejected"
  exit 1
fi
