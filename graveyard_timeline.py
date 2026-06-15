#!/usr/bin/env python3
"""
GRAVEYARD — multi-source timeline parity layer (memory + disk lite).

Cross-checks memory ghost PIDs/process names against a disk timeline export
(JSON or CSV: prefetch/bodyfile stub). Reports parity matches and gaps.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from graveyard_correlate import correlate


def load_timeline(path: Path) -> list[dict[str, str]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "entries" in data:
            return data["entries"]
        if isinstance(data, list):
            return data
        raise ValueError("JSON timeline must be {entries: [...]} or a list")

    if path.suffix.lower() == ".csv":
        entries: list[dict[str, str]] = []
        with path.open(encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entries.append({k: (v or "") for k, v in row.items()})
        return entries

    raise ValueError(f"Unsupported timeline format: {path.suffix} (use .json or .csv)")


def normalize_process(name: str) -> str:
    return name.lower().strip().replace("\\", "/")


def timeline_processes(entries: list[dict[str, str]]) -> set[str]:
    procs: set[str] = set()
    for entry in entries:
        for key in ("process", "Process", "image", "ImageFileName", "name"):
            val = entry.get(key, "")
            if val:
                procs.add(normalize_process(val))
        path_val = entry.get("path", entry.get("Path", ""))
        if path_val:
            procs.add(normalize_process(Path(path_val.replace("\\", "/")).name))
    return procs


def check_timeline_parity(
    exports_dir: Path,
    timeline_path: Path,
) -> dict[str, Any]:
    memory_report = correlate(exports_dir)
    timeline_entries = load_timeline(timeline_path)
    disk_procs = timeline_processes(timeline_entries)

    parity_results: list[dict[str, Any]] = []
    for ghost in memory_report.get("ghosts", []):
        image = normalize_process(str(ghost.get("image", "")))
        match = image in disk_procs
        parity_results.append({
            "type": "ghost_timeline_parity",
            "pid": ghost["pid"],
            "memory_image": ghost.get("image"),
            "disk_process_match": match,
            "status": "parity" if match else "memory_only",
            "interpretation_hint": (
                "Ghost process name also appears on disk timeline — corroboration candidate"
                if match
                else "Ghost PID not corroborated by disk timeline export — memory-only artifact"
            ),
        })

    memory_images = {
        normalize_process(str(g.get("image", "")))
        for g in memory_report.get("ghosts", [])
    }
    disk_only = sorted(disk_procs - memory_images - {"", "unknown"})

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "exports_dir": str(exports_dir.resolve()),
        "timeline_file": timeline_path.name,
        "timeline_entry_count": len(timeline_entries),
        "disk_process_count": len(disk_procs),
        "memory_ghost_count": len(memory_report.get("ghosts", [])),
        "parity_matches": sum(1 for p in parity_results if p["disk_process_match"]),
        "parity_gaps": sum(1 for p in parity_results if not p["disk_process_match"]),
        "ghost_timeline_parity": parity_results,
        "disk_only_processes": disk_only[:20],
        "memory_report_summary": memory_report.get("summary", {}),
    }


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
