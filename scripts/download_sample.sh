#!/usr/bin/env bash
# GRAVEYARD — attempt to fetch hackathon/SIFT memory samples; document manual fallback
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-/cases/graveyard/evidence}"
MEM_FILE="${TARGET}/mem.raw"

echo "=== GRAVEYARD Sample Download ==="
echo "Target: $TARGET"
echo ""

mkdir -p "$TARGET"

# Hackathon Egnyte / course share URLs (may require auth — documented in DATASETS.md)
EGNYTE_URLS=(
  "${GRAVEYARD_EGNYTE_URL:-}"
  "https://sansorg.egnyte.com/dl/FinDevil2026/memory/SRL-2018-mem.raw"
)

downloaded=0
for url in "${EGNYTE_URLS[@]}"; do
  [[ -z "$url" ]] && continue
  echo "Trying: $url"
  if command -v curl >/dev/null 2>&1; then
    if curl -fsSL --connect-timeout 15 -o "$MEM_FILE.part" "$url" 2>/dev/null; then
      mv "$MEM_FILE.part" "$MEM_FILE"
      echo "Downloaded: $MEM_FILE"
      downloaded=1
      break
    fi
  elif command -v wget >/dev/null 2>&1; then
    if wget -q -O "$MEM_FILE.part" "$url" 2>/dev/null; then
      mv "$MEM_FILE.part" "$MEM_FILE"
      echo "Downloaded: $MEM_FILE"
      downloaded=1
      break
    fi
  fi
  echo "  Failed (auth required or URL unavailable)"
done

if [[ "$downloaded" -eq 0 ]]; then
  cat <<'MANUAL'

=== Manual download required ===

Public / course memory samples (see docs/DATASETS.md for full URLs):

1. SANS SIFT VM — check /cases/ for bundled samples:
     ls -la /cases/

2. SANS course Egnyte (requires enrollment):
     Log in via https://www.sans.org/my-account/
     FOR508 / SRL-2018 → Memory images → copy to:
     sudo cp ~/Downloads/*.raw /cases/graveyard/evidence/mem.raw

3. Volatility Foundation samples:
     https://github.com/volatilityfoundation/volatility3/tree/develop/doc/sample

4. NIST CFReDS (disk-heavy; pair with memory if available):
     https://www.nist.gov/itl/ssd/software-quality-group/computer-forensics-reference-data-sets-cfreds

5. Magnet Forensics free samples:
     https://www.magnetforensics.com/blog/free-tools/

6. Set custom URL and retry:
     export GRAVEYARD_EGNYTE_URL='https://your-share-url/mem.raw'
     bash scripts/download_sample.sh

Offline benchmark (no memory file needed):
     python3 scripts/benchmark_accuracy.py --exports examples/sample_exports \\
       --ground-truth examples/ground_truth_srl2018_sample.json

MANUAL
  exit 1
fi

echo ""
echo "Verify image:"
file "$MEM_FILE" || true
sha256sum "$MEM_FILE" || shasum -a 256 "$MEM_FILE"
echo ""
echo "Next: bash scripts/run_live_triage.sh $MEM_FILE $(dirname "$TARGET")"
