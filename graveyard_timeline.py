#!/usr/bin/env python3
"""
GRAVEYARD — multi-source timeline parity layer (memory + disk lite).

Thin CLI wrapper around graveyard_engine.check_timeline_parity (backward compatible).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from graveyard_engine import check_timeline_parity


def main() -> int:
    parser = argparse.ArgumentParser(description="GRAVEYARD memory+disk timeline parity")
    parser.add_argument("--exports", type=Path, default=Path("./exports"))
    parser.add_argument("--timeline", type=Path, required=True, help="Disk timeline JSON or CSV")
    parser.add_argument("--output", type=Path, help="Write JSON report")
    args = parser.parse_args()

    if not args.exports.is_dir():
        print(f"ERROR: exports directory not found: {args.exports}", file=sys.stderr)
        return 1
    if not args.timeline.exists():
        print(f"ERROR: timeline file not found: {args.timeline}", file=sys.stderr)
        return 1

    try:
        report = check_timeline_parity(args.exports, args.timeline)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    output_json = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_json + "\n", encoding="utf-8")
        print(f"Timeline parity report: {args.output}")
    else:
        print(output_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
