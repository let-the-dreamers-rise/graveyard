#!/usr/bin/env bash
# GRAVEYARD — live memory triage pipeline for SANS SIFT Workstation
# Usage: bash scripts/run_live_triage.sh /path/to/mem.raw [case_dir]
set -euo pipefail

IMAGE="${1:?Usage: run_live_triage.sh <memory_image> [case_dir]}"
CASE_DIR="${2:-${CASE_ROOT:-$(pwd)}}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TS="$(date +%Y%m%d_%H%M%S)"

# Evidence protection — never write to these patterns
EVIDENCE_PATTERNS=(
  "/cases/*/evidence/"
  "/mnt/"
  ".raw"
  ".vmem"
  ".dmp"
)

if [[ ! -f "$IMAGE" ]]; then
  echo "ERROR: memory image not found: $IMAGE" >&2
  exit 1
fi

for pat in "${EVIDENCE_PATTERNS[@]}"; do
  if [[ "$CASE_DIR" == *"$pat"* ]] && [[ "$CASE_DIR" == "$IMAGE" ]]; then
    echo "ERROR: case_dir must not equal evidence image path" >&2
    exit 1
  fi
done

mkdir -p "$CASE_DIR"/{exports,analysis,reports,docs/execution_logs}

cd "$CASE_DIR"
echo "=== GRAVEYARD Live Triage ==="
echo "Image:  $IMAGE"
echo "Case:   $CASE_DIR"
echo "Time:   $TS"
echo ""

# 1. Evidence inventory
echo "[1/9] Evidence inventory"
{
  echo "# GRAVEYARD evidence inventory — $TS"
  file "$IMAGE"
  sha256sum "$IMAGE"
  ls -lh "$IMAGE"
} 2>&1 | tee "exports/evidence_inventory_${TS}.txt"

# 2. Profile
echo "[2/9] windows.info"
vol.py -f "$IMAGE" windows.info 2>&1 | tee "exports/windows_info_${TS}.txt"

# 3. Process baseline
echo "[3/9] windows.pslist"
vol.py -f "$IMAGE" windows.pslist 2>&1 | tee "exports/pslist_${TS}.txt"

# 4. Hidden process scan
echo "[4/9] windows.psscan"
vol.py -f "$IMAGE" windows.psscan 2>&1 | tee "exports/psscan_${TS}.txt"

# 5. Ghost correlation (before netscan — ghost-first)
echo "[5/9] graveyard_correlate"
python3 "$REPO_DIR/graveyard_correlate.py" \
  --exports ./exports/ \
  --output "analysis/graveyard_report_${TS}.json" \
  2>&1 | tee "docs/execution_logs/graveyard_correlate_${TS}.jsonl"

# 6. Network scan
echo "[6/9] windows.netscan"
vol.py -f "$IMAGE" windows.netscan 2>&1 | tee "exports/netscan_${TS}.txt"

# Re-correlate with netscan present
echo "[6b/9] graveyard_correlate (with netscan)"
python3 "$REPO_DIR/graveyard_correlate.py" \
  --exports ./exports/ \
  --output "analysis/graveyard_report_${TS}.json" \
  2>&1 | tee -a "docs/execution_logs/graveyard_correlate_${TS}.jsonl"

# 7. Optional disk timeline parity (if timeline artifact provided)
TIMELINE="${DISK_TIMELINE:-}"
if [[ -n "$TIMELINE" && -f "$TIMELINE" ]]; then
  echo "[7/9] graveyard_timeline parity"
  python3 "$REPO_DIR/graveyard_timeline.py" \
    --exports ./exports/ \
    --timeline "$TIMELINE" \
    --output "analysis/timeline_parity_${TS}.json" \
    2>&1 | tee "docs/execution_logs/timeline_parity_${TS}.jsonl"
else
  echo "[7/9] graveyard_timeline — skipped (set DISK_TIMELINE=/path/to/timeline.json to enable)"
fi

# 8. Malfind on ghost PIDs (full scan — agent can filter manually)
echo "[8/9] windows.malfind"
vol.py -f "$IMAGE" windows.malfind 2>&1 | tee "exports/malfind_${TS}.txt"

# 9. Generate audit log + findings template
echo "[9/9] Audit log + findings template"
python3 "$REPO_DIR/scripts/generate_audit_log.py" \
  --exports ./exports/ \
  --output "docs/execution_logs/execution_log_${TS}.jsonl"

python3 "$REPO_DIR/scripts/generate_findings_template.py" \
  --graveyard-report "analysis/graveyard_report_${TS}.json" \
  --output "findings_draft_template_${TS}.json" 2>/dev/null || \
  cp "$REPO_DIR/schema/finding.schema.json" "findings_draft_template_${TS}.schema.json"

echo ""
echo "=== Triage complete ==="
echo "  Graveyard report: analysis/graveyard_report_${TS}.json"
echo "  Audit log:        docs/execution_logs/execution_log_${TS}.jsonl"
echo "  Next: draft findings_draft.json → verify_findings.py"
echo ""
echo "Verify command:"
echo "  python3 $REPO_DIR/verify_findings.py findings_draft.json \\"
echo "    --exports ./exports --report ./reports/report.md"
