#!/usr/bin/env python3
"""
GRAVEYARD — deterministic ghost-artifact correlator for Protocol SIFT.

Thin CLI wrapper around graveyard_engine.correlate (backward compatible).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from graveyard_engine import correlate


def main() -> int:
    parser = argparse.ArgumentParser(description="GRAVEYARD ghost-artifact correlator")
    parser.add_argument("--exports", type=Path, default=Path("./exports"), help="Directory of Volatility exports")
    parser.add_argument("--output", type=Path, help="Write JSON report to file (default: stdout)")
    parser.add_argument("--json-out", action="store_true", help="Alias for stdout JSON output")
    args = parser.parse_args()

    if not args.exports.is_dir():
        print(f"ERROR: exports directory not found: {args.exports}", file=sys.stderr)
        return 1

    try:
        report = correlate(args.exports)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    report.pop("_pslist_images", None)
    output_json = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_json + "\n", encoding="utf-8")
        print(f"GRAVEYARD report written: {args.output}")
    else:
        print(output_json)

    return 0


if __name__ == "__main__":
    sys.exit(main())
