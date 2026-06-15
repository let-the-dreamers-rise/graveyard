#!/usr/bin/env python3
"""
GRAVEYARD — generate realistic JSONL audit log from exports/ with sha256 hashes.

Each line: timestamp, event, export_file, sha256, size_bytes, inferred_command.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PLUGIN_MAP = {
    "windows_info": "vol.py -f <image> windows.info",
    "pslist": "vol.py -f <image> windows.pslist",
    "psscan": "vol.py -f <image> windows.psscan",
    "netscan": "vol.py -f <image> windows.netscan",
    "malfind": "vol.py -f <image> windows.malfind",
    "evidence_inventory": "file + sha256sum <image>",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def infer_command(filename: str) -> str:
    lower = filename.lower()
    for key, cmd in PLUGIN_MAP.items():
        if key in lower:
            return cmd
    if "graveyard" in lower:
        return "python3 graveyard_correlate.py --exports ./exports/"
    return "unknown"


def extract_timestamp(filename: str) -> str | None:
    match = re.search(r"(\d{8}_\d{6})", filename)
    if match:
        raw = match.group(1)
        try:
            dt = datetime.strptime(raw, "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            pass
    return None


def generate_log(exports_dir: Path, case_id: str = "CASE-001") -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc).isoformat()

    events.append({
        "timestamp": now,
        "event": "audit_log_start",
        "case_id": case_id,
        "exports_dir": str(exports_dir.resolve()),
    })

    for export_path in sorted(exports_dir.glob("*")):
        if not export_path.is_file():
            continue
        file_ts = extract_timestamp(export_path.name) or now
        stat = export_path.stat()
        events.append({
            "timestamp": file_ts,
            "event": "export_captured",
            "export_file": export_path.name,
            "sha256": sha256_file(export_path),
            "size_bytes": stat.st_size,
            "inferred_command": infer_command(export_path.name),
            "read_only_evidence": True,
        })

    events.append({
        "timestamp": now,
        "event": "audit_log_complete",
        "export_count": sum(1 for e in events if e.get("event") == "export_captured"),
    })
    return events


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate JSONL audit log from exports/")
    parser.add_argument("--exports", type=Path, default=Path("./exports"))
    parser.add_argument("--output", type=Path, default=Path("./docs/execution_logs/execution_log.jsonl"))
    parser.add_argument("--case-id", default="CASE-001")
    parser.add_argument("--append", action="store_true", help="Append to existing log")
    args = parser.parse_args()

    if not args.exports.is_dir():
        print(f"ERROR: exports directory not found: {args.exports}", file=sys.stderr)
        return 1

    events = generate_log(args.exports, args.case_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if args.append else "w"
    with args.output.open(mode, encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    print(f"Audit log written: {args.output} ({len(events)} events)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
