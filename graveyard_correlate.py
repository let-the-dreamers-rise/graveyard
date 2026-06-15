#!/usr/bin/env python3
"""
GRAVEYARD — deterministic ghost-artifact correlator for Protocol SIFT.

Parses Volatility export files in ./exports/ and detects:
  - ghost_process: PID in psscan but NOT in pslist
  - orphan_socket: netscan PID with ESTABLISHED connection but PID not in pslist

Output JSON: {"ghosts": [...], "orphan_sockets": [...]} with citations to export lines.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def find_export(exports_dir: Path, prefix: str) -> Path | None:
    matches = sorted(exports_dir.glob(f"{prefix}*.txt"))
    if not matches:
        matches = sorted(exports_dir.glob(f"*{prefix}*.txt"))
    return matches[-1] if matches else None


def parse_process_table(path: Path) -> dict[int, dict[str, str]]:
    """Parse Volatility pslist/psscan tabular output into {pid: row_fields}."""
    processes: dict[int, dict[str, str]] = {}
    text = path.read_text(encoding="utf-8", errors="replace")
    header_seen = False

    for line_num, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("Volatility") or stripped.startswith("Progress:"):
            continue
        if stripped.startswith("PID") and "PPID" in stripped:
            header_seen = True
            continue
        if not header_seen:
            continue

        parts = re.split(r"\t+", stripped)
        if len(parts) < 3:
            continue

        try:
            pid = int(parts[0])
        except ValueError:
            continue

        processes[pid] = {
            "pid": parts[0],
            "ppid": parts[1],
            "image": parts[2],
            "raw_line": stripped,
            "line_number": str(line_num),
            "export_file": path.name,
        }

    return processes


def parse_netscan(path: Path) -> list[dict[str, str]]:
    """Parse Volatility netscan output into connection records."""
    connections: list[dict[str, str]] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    header_seen = False

    for line_num, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("Volatility") or stripped.startswith("Progress:"):
            continue
        if "Foreign Address" in stripped and "State" in stripped:
            header_seen = True
            continue
        if not header_seen:
            continue

        parts = re.split(r"\t+", stripped)
        if len(parts) < 7:
            continue

        try:
            pid = int(parts[1])
        except ValueError:
            continue

        connections.append({
            "pid": parts[1],
            "local_address": parts[2],
            "foreign_address": parts[3],
            "foreign_port": parts[4],
            "state": parts[5],
            "owner": parts[7] if len(parts) > 7 else "",
            "raw_line": stripped,
            "line_number": str(line_num),
            "export_file": path.name,
        })

    return connections


def correlate(exports_dir: Path) -> dict[str, Any]:
    psscan_path = find_export(exports_dir, "psscan_")
    pslist_path = find_export(exports_dir, "pslist_")
    netscan_path = find_export(exports_dir, "netscan_")

    missing = []
    if not psscan_path:
        missing.append("psscan")
    if not pslist_path:
        missing.append("pslist")
    if missing:
        raise FileNotFoundError(f"Required export(s) not found in {exports_dir}: {', '.join(missing)}")

    psscan = parse_process_table(psscan_path)
    pslist = parse_process_table(pslist_path)
    pslist_pids = set(pslist.keys())

    ghosts: list[dict[str, Any]] = []
    for pid, row in sorted(psscan.items()):
        if pid not in pslist_pids:
            ghosts.append({
                "type": "ghost_process",
                "pid": pid,
                "ppid": int(row["ppid"]) if row["ppid"].isdigit() else row["ppid"],
                "image": row["image"],
                "citations": [
                    {
                        "export_file": row["export_file"],
                        "line_number": int(row["line_number"]),
                        "matched_text": row["raw_line"],
                    }
                ],
            })

    orphan_sockets: list[dict[str, Any]] = []
    if netscan_path:
        for conn in parse_netscan(netscan_path):
            if conn["state"].upper() != "ESTABLISHED":
                continue
            pid = int(conn["pid"])
            if pid not in pslist_pids:
                orphan_sockets.append({
                    "type": "orphan_socket",
                    "pid": pid,
                    "local_address": conn["local_address"],
                    "foreign_address": conn["foreign_address"],
                    "foreign_port": conn["foreign_port"],
                    "state": conn["state"],
                    "owner": conn["owner"],
                    "citations": [
                        {
                            "export_file": conn["export_file"],
                            "line_number": int(conn["line_number"]),
                            "matched_text": conn["raw_line"],
                        }
                    ],
                })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "exports_dir": str(exports_dir.resolve()),
        "sources": {
            "psscan": psscan_path.name if psscan_path else None,
            "pslist": pslist_path.name if pslist_path else None,
            "netscan": netscan_path.name if netscan_path else None,
        },
        "summary": {
            "pslist_count": len(pslist),
            "psscan_count": len(psscan),
            "ghost_count": len(ghosts),
            "orphan_socket_count": len(orphan_sockets),
        },
        "ghosts": ghosts,
        "orphan_sockets": orphan_sockets,
    }


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
