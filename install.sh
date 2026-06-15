#!/usr/bin/env bash
# GRAVEYARD — ghost-artifact hunter for Protocol SIFT on SANS SIFT Workstation
set -euo pipefail

REPO_DIR="${GRAVEYARD_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
CASE_ROOT="${CASE_ROOT:-/cases/graveyard}"

echo "=== GRAVEYARD Installer ==="
echo "Repo: $REPO_DIR"

# 1. Protocol SIFT (if not already installed)
if [[ ! -f "$HOME/.claude/CLAUDE.md" ]] || ! grep -q "Protocol SIFT" "$HOME/.claude/CLAUDE.md" 2>/dev/null; then
  echo "Installing Protocol SIFT..."
  curl -fsSL https://raw.githubusercontent.com/teamdfir/protocol-sift/main/install.sh | bash
else
  echo "Protocol SIFT already present — skipping"
fi

# 2. Case workspace
sudo mkdir -p "$CASE_ROOT"/{exports,analysis,reports,docs/execution_logs}
sudo chown -R "$(whoami):$(whoami)" "$CASE_ROOT" 2>/dev/null || true

# 3. Copy GRAVEYARD tooling
cp "$REPO_DIR/graveyard_correlate.py" "$CASE_ROOT/"
cp "$REPO_DIR/graveyard_timeline.py" "$CASE_ROOT/" 2>/dev/null || true
cp "$REPO_DIR/verify_findings.py" "$CASE_ROOT/"
cp "$REPO_DIR/spoliation_guard.py" "$CASE_ROOT/" 2>/dev/null || true
cp "$REPO_DIR/mcp_graveyard_server.py" "$CASE_ROOT/" 2>/dev/null || true
cp -r "$REPO_DIR/scripts" "$CASE_ROOT/" 2>/dev/null || true
cp "$REPO_DIR/run_demo.sh" "$CASE_ROOT/" 2>/dev/null || true
cp "$REPO_DIR/requirements.txt" "$CASE_ROOT/" 2>/dev/null || true
cp "$REPO_DIR/schema/finding.schema.json" "$CASE_ROOT/"
cp -r "$REPO_DIR/examples/sample_exports"/* "$CASE_ROOT/exports/" 2>/dev/null || mkdir -p "$CASE_ROOT/exports"

# 4. Cursor / agent rules
mkdir -p "$CASE_ROOT/.cursor/rules"
cp "$REPO_DIR/.cursor/rules/graveyard.mdc" "$CASE_ROOT/.cursor/rules/" 2>/dev/null || true
cp "$REPO_DIR/AGENTS.md" "$CASE_ROOT/"

# 5. Settings note
SETTINGS="$HOME/.claude/settings.json"
if [[ -f "$SETTINGS" ]]; then
  echo "Note: Review $SETTINGS — GRAVEYARD uses ./exports, ./analysis, ./reports only"
fi

cat <<EOF

=== GRAVEYARD install complete ===

Case directory: $CASE_ROOT
  exports/   — raw tool output (tee here)
  analysis/  — agent working files
  reports/   — verified reports only

Quick test (offline with sample data):
  cd $REPO_DIR
  pip install -r requirements.txt 2>/dev/null || true
  bash run_demo.sh

Memory triage workflow:
  1. Open case in Cursor with AGENTS.md
  2. bash scripts/run_live_triage.sh /cases/graveyard/evidence/mem.raw /cases/graveyard
     OR run Volatility plugins manually; tee all output to exports/
  3. Run graveyard_correlate.py — hunt ghosts before netscan deep-dive
  4. Draft findings JSON → verify_findings.py
  5. python3 scripts/benchmark_accuracy.py --exports ./exports --ground-truth examples/ground_truth_srl2018_sample.json
  6. On REJECT: fix and re-run (max 3 iterations)

EOF
