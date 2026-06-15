#!/usr/bin/env bash
# GRAVEYARD — deterministic autonomous self-correction loop (no LLM)
# engine → draft findings from facts → verify → auto-correct → verify (max 3 iter)
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPORTS="${1:-examples/sample_exports}"
TIMELINE="${2:-}"
CASE_DIR="${3:-$REPO_DIR}"
MAX_ITER="${MAX_ITER:-3}"
DEMO_INJECT="${DEMO_INJECT:-1}"
TS="$(date +%Y%m%d_%H%M%S)"

cd "$CASE_DIR"
mkdir -p analysis reports docs/execution_logs

echo "=== GRAVEYARD Agent Loop (deterministic self-correction) ==="
echo "Exports:  $EXPORTS"
echo "Timeline: ${TIMELINE:-none}"
echo "Case:     $CASE_DIR"
echo "Max iter: $MAX_ITER"
echo ""

# Step 1: Unified engine
echo "[1] graveyard_engine"
ENGINE_OUT="analysis/graveyard_engine_${TS}.json"
ENGINE_ARGS=(--exports "$EXPORTS" --output "$ENGINE_OUT")
if [[ -n "$TIMELINE" && -f "$TIMELINE" ]]; then
  ENGINE_ARGS+=(--timeline "$TIMELINE")
fi
python3 "$REPO_DIR/graveyard_engine.py" "${ENGINE_ARGS[@]}"

# Step 2: Initial draft (inject attribution violation for tiebreaker demo)
DRAFT="findings_draft_${TS}.json"
echo "[2] generate findings from engine facts"
DRAFT_ARGS=(
  --exports "$EXPORTS"
  --engine-report "$ENGINE_OUT"
  --output "$DRAFT"
)
if [[ -n "$TIMELINE" && -f "$TIMELINE" ]]; then
  DRAFT_ARGS+=(--timeline "$TIMELINE")
fi
if [[ "$DEMO_INJECT" == "1" ]]; then
  echo "      (demo mode: injecting attribution violation for self-correction proof)"
  DRAFT_ARGS+=(--inject-bad)
fi
python3 "$REPO_DIR/scripts/auto_correct_findings.py" "${DRAFT_ARGS[@]}"

AUDIT_LOG="docs/execution_logs/agent_loop_${TS}.jsonl"
CURRENT="$DRAFT"
FINAL_EXIT=1

# Steps 3-N: verify → auto-correct loop (max MAX_ITER)
for ((iter=1; iter<=MAX_ITER; iter++)); do
  echo ""
  echo "[verify $iter/$MAX_ITER] $CURRENT"
  set +e
  VERIFY_ARGS=("$CURRENT" --exports "$EXPORTS" --audit-log "$AUDIT_LOG" --report "reports/report_${TS}.md")
  python3 "$REPO_DIR/verify_findings.py" "${VERIFY_ARGS[@]}" \
    2>&1 | tee "docs/execution_logs/agent_loop_v${iter}_${TS}.txt"
  V_EXIT=$?
  set -e
  echo "      exit code: $V_EXIT"

  if [[ "$V_EXIT" -eq 0 ]]; then
    FINAL_EXIT=0
    echo ""
    echo "=== Agent Loop Complete — PASS on iteration $iter ==="
    break
  fi

  if [[ "$iter" -ge "$MAX_ITER" ]]; then
    echo ""
    echo "=== Agent Loop Complete — FAIL after $MAX_ITER iteration(s) ==="
    break
  fi

  CORRECTED="findings_corrected_iter${iter}_${TS}.json"
  echo "[auto-correct $iter/$MAX_ITER] rebuild from engine facts (no LLM)"
  CORRECT_ARGS=(
    --exports "$EXPORTS"
    --engine-report "$ENGINE_OUT"
    --output "$CORRECTED"
  )
  if [[ -n "$TIMELINE" && -f "$TIMELINE" ]]; then
    CORRECT_ARGS+=(--timeline "$TIMELINE")
  fi
  python3 "$REPO_DIR/scripts/auto_correct_findings.py" "${CORRECT_ARGS[@]}"
  CURRENT="$CORRECTED"
done

echo ""
echo "  Engine report:  $ENGINE_OUT"
echo "  Final findings: $CURRENT"
echo "  Audit log:      $AUDIT_LOG"
if [[ "$FINAL_EXIT" -eq 0 ]]; then
  echo "  Report:         reports/report_${TS}.md"
  echo ""
  echo "RESULT: PASS — deterministic self-correction demonstrated"
else
  echo ""
  echo "RESULT: FAIL — findings still rejected after $MAX_ITER iteration(s)"
fi
exit "$FINAL_EXIT"
