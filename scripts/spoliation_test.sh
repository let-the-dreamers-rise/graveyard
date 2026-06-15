#!/usr/bin/env bash
# GRAVEYARD spoliation test runner (SIFT/Linux)
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"
echo "=== GRAVEYARD Spoliation Tests ==="
python3 -m pytest tests/test_spoliation.py -v 2>/dev/null || python3 tests/test_spoliation.py
echo "=== Spoliation tests complete ==="
