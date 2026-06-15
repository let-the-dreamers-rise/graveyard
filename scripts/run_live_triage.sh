#!/usr/bin/env bash
# GRAVEYARD — live memory triage pipeline for SANS SIFT Workstation
# Usage: bash scripts/run_live_triage.sh /path/to/mem.raw [case_dir]
set -euo pipefail

IMAGE="${1:?Usage: run_live_triage.sh <memory_image> [case_dir]}"
CASE_DIR="${2:-${CASE_ROOT:-$(pwd)}}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TS="$(date +%Y%m%d_%H%M%S)"
TOTAL_STEPS=10
STEP=0

# Evidence protection — never write to these patterns
EVIDENCE_PATTERNS=(
  "/cases/*/evidence/"
  "/mnt/"
  ".raw"
  ".vmem"
  ".dmp"
)

log_step() {
  STEP=$((STEP + 1))
  echo ""
  echo "[$STEP/$TOTAL_STEPS] $*"
  echo "----------------------------------------"
}

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

find_vol() {
  local candidates=(
    "${VOLPY:-}"
    "$(command -v vol.py 2>/dev/null || true)"
    "$(command -v vol 2>/dev/null || true)"
    "/usr/local/bin/vol.py"
    "$HOME/.local/bin/vol.py"
    "/opt/volatility3/vol.py"
  )
  for c in "${candidates[@]}"; do
    [[ -n "$c" && -x "$c" ]] && { echo "$c"; return 0; }
    [[ -n "$c" ]] && command -v "$c" >/dev/null 2>&1 && { echo "$c"; return 0; }
  done
  return 1
}

run_vol() {
  local plugin="$1"
  local outfile="$2"
  if ! "$VOLPY" -f "$IMAGE" "$plugin" 2>&1 | tee "$outfile"; then
    fail "Volatility plugin failed: $plugin (see $outfile)"
  fi
}

run_python() {
  if command -v python3 >/dev/null 2>&1; then
    python3 "$@"
  else
    python "$@"
  fi
}

[[ -f "$IMAGE" ]] || fail "memory image not found: $IMAGE"

for pat in "${EVIDENCE_PATTERNS[@]}"; do
  if [[ "$CASE_DIR" == *"$pat"* ]] && [[ "$CASE_DIR" == "$IMAGE" ]]; then
    fail "case_dir must not equal evidence image path"
  fi
done

VOLPY="$(find_vol)" || fail "vol.py not found. Set VOLPY=/path/to/vol.py or install Volatility 3"
echo "Using vol.py: $VOLPY"

mkdir -p "$CASE_DIR"/{exports,analysis,reports,docs/execution_logs} || fail "cannot create case directories under $CASE_DIR"

cd "$CASE_DIR"
echo "=== GRAVEYARD Live Triage ==="
echo "Image:  $IMAGE"
echo "Case:   $CASE_DIR"
echo "Repo:   $REPO_DIR"
echo "Time:   $TS"
echo "Vol:    $VOLPY"

# 1. Evidence inventory
log_step "Evidence inventory"
{
  echo "# GRAVEYARD evidence inventory — $TS"
  file "$IMAGE" || true
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$IMAGE"
  else
    shasum -a 256 "$IMAGE" || certutil -hashfile "$IMAGE" SHA256 2>/dev/null || true
  fi
  ls -lh "$IMAGE" 2>/dev/null || dir "$IMAGE"
} 2>&1 | tee "exports/evidence_inventory_${TS}.txt"

# 2. Profile
log_step "windows.info"
run_vol "windows.info" "exports/windows_info_${TS}.txt"

# 3. Process baseline
log_step "windows.pslist"
run_vol "windows.pslist" "exports/pslist_${TS}.txt"

# 4. Hidden process scan
log_step "windows.psscan"
run_vol "windows.psscan" "exports/psscan_${TS}.txt"

# 5. Ghost correlation (before netscan — ghost-first)
log_step "graveyard_engine (initial)"
run_python "$REPO_DIR/graveyard_engine.py" \
  --exports ./exports/ \
  --output "analysis/graveyard_engine_${TS}.json" \
  2>&1 | tee "docs/execution_logs/graveyard_engine_${TS}.jsonl"

# 6. Network scan
log_step "windows.netscan"
run_vol "windows.netscan" "exports/netscan_${TS}.txt"

# Re-run engine with netscan present
log_step "graveyard_engine (with netscan)"
run_python "$REPO_DIR/graveyard_engine.py" \
  --exports ./exports/ \
  --output "analysis/graveyard_engine_${TS}.json" \
  2>&1 | tee -a "docs/execution_logs/graveyard_engine_${TS}.jsonl"

# Legacy correlate output for backward compatibility
run_python "$REPO_DIR/graveyard_correlate.py" \
  --exports ./exports/ \
  --output "analysis/graveyard_report_${TS}.json" \
  2>&1 | tee -a "docs/execution_logs/graveyard_correlate_${TS}.jsonl"

# 7. Optional disk timeline parity
TIMELINE="${DISK_TIMELINE:-}"
if [[ -n "$TIMELINE" && -f "$TIMELINE" ]]; then
  log_step "graveyard_engine timeline parity"
  run_python "$REPO_DIR/graveyard_engine.py" \
    --exports ./exports/ \
    --timeline "$TIMELINE" \
    --output "analysis/graveyard_engine_${TS}.json" \
    2>&1 | tee "docs/execution_logs/timeline_parity_${TS}.jsonl"
else
  log_step "timeline parity — skipped (set DISK_TIMELINE=/path/to/timeline.json)"
fi

# 8. Malfind
log_step "windows.malfind"
run_vol "windows.malfind" "exports/malfind_${TS}.txt"

# 9. Audit log + findings template
log_step "Audit log + findings template"
run_python "$REPO_DIR/scripts/generate_audit_log.py" \
  --exports ./exports/ \
  --output "docs/execution_logs/execution_log_${TS}.jsonl"

run_python "$REPO_DIR/scripts/generate_findings_template.py" \
  --graveyard-report "analysis/graveyard_report_${TS}.json" \
  --output "findings_draft_template_${TS}.json" 2>/dev/null || \
  cp "$REPO_DIR/schema/finding.schema.json" "findings_draft_template_${TS}.schema.json"

# 10. Summary
log_step "Triage complete"
echo ""
echo "=== Outputs ==="
echo "  Engine report:    analysis/graveyard_engine_${TS}.json"
echo "  Correlate report: analysis/graveyard_report_${TS}.json"
echo "  Audit log:        docs/execution_logs/execution_log_${TS}.jsonl"
echo "  Findings template: findings_draft_template_${TS}.json"
echo ""
echo "Next steps:"
echo "  1. Fill examples/ground_truth_live_template.json with PIDs from engine report"
echo "  2. Draft findings_draft.json → verify_findings.py"
echo "  3. bash $REPO_DIR/scripts/agent_loop.sh ./exports"
echo ""
echo "Verify command:"
echo "  run_python $REPO_DIR/verify_findings.py findings_draft.json \\"
echo "    --exports ./exports --report ./reports/report.md"
