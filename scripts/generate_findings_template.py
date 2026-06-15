#!/usr/bin/env python3
"""Generate a findings_draft.json skeleton from graveyard_correlate output."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def build_template(report_path: Path) -> dict:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    findings = []
    idx = 1

    for ghost in report.get("ghosts", []):
        cite = ghost["citations"][0] if ghost.get("citations") else {}
        findings.append({
            "id": f"F{idx:03d}",
            "observation": (
                f"PID {ghost['pid']} ({ghost.get('image', 'unknown')}) appears in psscan "
                "output but is absent from pslist active process listing."
            ),
            "interpretation": (
                "Possible hidden or terminated process artifact — requires malfind "
                "and network corroboration."
            ),
            "confidence": "inferred",
            "citations": [
                {
                    "export_file": cite.get("export_file", "psscan_*.txt"),
                    "matched_text": cite.get("matched_text", str(ghost["pid"])),
                }
            ],
            "tool_provenance": {
                "command": "vol.py windows.psscan; vol.py windows.pslist; graveyard_correlate.py",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        })
        idx += 1

    for orphan in report.get("orphan_sockets", []):
        cite = orphan["citations"][0] if orphan.get("citations") else {}
        findings.append({
            "id": f"F{idx:03d}",
            "observation": (
                f"PID {orphan['pid']} has an ESTABLISHED TCP connection to "
                f"{orphan.get('foreign_address', '?')} on port {orphan.get('foreign_port', '?')} "
                "but PID is absent from pslist."
            ),
            "interpretation": (
                "Orphan socket — network connection without active process listing."
            ),
            "confidence": "inferred",
            "citations": [
                {
                    "export_file": cite.get("export_file", "netscan_*.txt"),
                    "matched_text": cite.get("matched_text", str(orphan["pid"])),
                }
            ],
            "tool_provenance": {
                "command": "vol.py windows.netscan; graveyard_correlate.py",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        })
        idx += 1

    return {"findings": findings}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate findings template from correlate report")
    parser.add_argument("--graveyard-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not args.graveyard_report.exists():
        print(f"ERROR: report not found: {args.graveyard_report}", file=sys.stderr)
        return 1

    template = build_template(args.graveyard_report)
    args.output.write_text(json.dumps(template, indent=2) + "\n", encoding="utf-8")
    print(f"Findings template written: {args.output} ({len(template['findings'])} finding(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
