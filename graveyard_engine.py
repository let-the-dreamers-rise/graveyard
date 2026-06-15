#!/usr/bin/env python3
"""
GRAVEYARD — unified correlation engine (ghost + orphan + timeline + contradictions).

Merges graveyard_correlate.py and graveyard_timeline.py into one scored report.
Backward-compatible: graveyard_correlate.correlate and graveyard_timeline.check_timeline_parity
re-export from this module.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Severity weights (deterministic, documented for judges)
SEVERITY_GHOST = 50
SEVERITY_ORPHAN = 60
SEVERITY_GHOST_ORPHAN_COMBO = 90
SEVERITY_CONTRADICTION = 85
SEVERITY_TIMELINE_PARITY_BONUS = 10


def find_export(exports_dir: Path, prefix: str) -> Path | None:
    matches = sorted(exports_dir.glob(f"{prefix}*.txt"))
    if not matches:
        matches = sorted(exports_dir.glob(f"*{prefix}*.txt"))
    return matches[-1] if matches else None


def parse_process_table(path: Path) -> dict[int, dict[str, str]]:
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
            int(parts[1])
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
    """Ghost processes + orphan sockets from Volatility exports."""
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
        "_pslist_images": {pid: row["image"] for pid, row in pslist.items()},
    }


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


def deleted_timeline_processes(entries: list[dict[str, str]]) -> set[str]:
    """Processes marked deleted on disk timeline."""
    deleted: set[str] = set()
    for entry in entries:
        status = (entry.get("status") or entry.get("Status") or entry.get("action") or "").lower()
        if status not in ("deleted", "removed", "unlinked"):
            continue
        for key in ("process", "Process", "image", "ImageFileName", "name"):
            val = entry.get(key, "")
            if val:
                deleted.add(normalize_process(val))
        path_val = entry.get("path", entry.get("Path", ""))
        if path_val:
            deleted.add(normalize_process(Path(path_val.replace("\\", "/")).name))
    return deleted


def compute_artifact_severity(
    artifact_type: str,
    pid: int,
    ghost_pids: set[int],
    orphan_pids: set[int],
    has_timeline_parity: bool = False,
) -> dict[str, Any]:
    """Deterministic severity score for ranked findings."""
    base = SEVERITY_GHOST if artifact_type == "ghost_process" else SEVERITY_ORPHAN
    elevated = pid in ghost_pids and pid in orphan_pids
    if elevated:
        base = SEVERITY_GHOST_ORPHAN_COMBO
        priority = "critical"
    elif artifact_type == "orphan_socket":
        priority = "high"
    else:
        priority = "medium"

    score = base
    if has_timeline_parity:
        score += SEVERITY_TIMELINE_PARITY_BONUS

    return {
        "severity_score": score,
        "priority": priority,
        "elevated": elevated,
        "reason": (
            "Ghost process with orphan ESTABLISHED socket — network without live process listing"
            if elevated
            else f"{artifact_type} detected by correlate"
        ),
    }


def detect_contradictions(
    memory_report: dict[str, Any],
    timeline_entries: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """
    Contradiction: process appears running in pslist but disk timeline marks deleted.
    """
    pslist_images = memory_report.get("_pslist_images", {})
    deleted_on_disk = deleted_timeline_processes(timeline_entries)
    contradictions: list[dict[str, Any]] = []

    for pid, image in pslist_images.items():
        norm = normalize_process(image)
        if norm in deleted_on_disk:
            contradictions.append({
                "type": "memory_disk_contradiction",
                "pid": pid,
                "memory_image": image,
                "memory_status": "running_in_pslist",
                "disk_status": "deleted_on_timeline",
                "severity_score": SEVERITY_CONTRADICTION,
                "priority": "high",
                "interpretation_hint": (
                    "Process listed as active in memory pslist but marked deleted on disk timeline"
                ),
            })

    return contradictions


def check_timeline_parity(exports_dir: Path, timeline_path: Path) -> dict[str, Any]:
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
    contradictions = detect_contradictions(memory_report, timeline_entries)

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
        "contradictions": contradictions,
        "disk_only_processes": disk_only[:20],
        "memory_report_summary": memory_report.get("summary", {}),
    }


def run_engine(
    exports_dir: Path,
    timeline_path: Path | None = None,
) -> dict[str, Any]:
    """Unified GRAVEYARD report with severity-ranked artifacts."""
    memory = correlate(exports_dir)
    ghost_pids = {g["pid"] for g in memory.get("ghosts", [])}
    orphan_pids = {o["pid"] for o in memory.get("orphan_sockets", [])}

    parity_map: dict[int, bool] = {}
    contradictions: list[dict[str, Any]] = []
    timeline_meta: dict[str, Any] | None = None

    if timeline_path and timeline_path.exists():
        timeline_report = check_timeline_parity(exports_dir, timeline_path)
        timeline_meta = {
            "timeline_file": timeline_path.name,
            "parity_matches": timeline_report["parity_matches"],
            "parity_gaps": timeline_report["parity_gaps"],
        }
        for p in timeline_report.get("ghost_timeline_parity", []):
            parity_map[p["pid"]] = p["disk_process_match"]
        contradictions = timeline_report.get("contradictions", [])

    ranked_artifacts: list[dict[str, Any]] = []

    for ghost in memory.get("ghosts", []):
        pid = ghost["pid"]
        sev = compute_artifact_severity(
            "ghost_process", pid, ghost_pids, orphan_pids, parity_map.get(pid, False)
        )
        ranked_artifacts.append({**ghost, **sev, "timeline_parity": parity_map.get(pid)})

    for orphan in memory.get("orphan_sockets", []):
        pid = orphan["pid"]
        sev = compute_artifact_severity(
            "orphan_socket", pid, ghost_pids, orphan_pids, parity_map.get(pid, False)
        )
        ranked_artifacts.append({**orphan, **sev, "timeline_parity": parity_map.get(pid)})

    for contra in contradictions:
        ranked_artifacts.append(contra)

    ranked_artifacts.sort(key=lambda a: a.get("severity_score", 0), reverse=True)

    report = {
        "engine": "graveyard_engine",
        "version": "2.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "exports_dir": str(exports_dir.resolve()),
        "sources": memory.get("sources", {}),
        "summary": {
            **memory.get("summary", {}),
            "contradiction_count": len(contradictions),
            "max_severity": ranked_artifacts[0]["severity_score"] if ranked_artifacts else 0,
            "critical_count": sum(1 for a in ranked_artifacts if a.get("priority") == "critical"),
        },
        "timeline": timeline_meta,
        "ghosts": memory.get("ghosts", []),
        "orphan_sockets": memory.get("orphan_sockets", []),
        "contradictions": contradictions,
        "ranked_artifacts": ranked_artifacts,
    }
    # Strip internal fields
    report.pop("_pslist_images", None)
    if "_pslist_images" in memory:
        del memory["_pslist_images"]
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="GRAVEYARD unified correlation engine")
    parser.add_argument("--exports", type=Path, default=Path("./exports"))
    parser.add_argument("--timeline", type=Path, help="Optional disk timeline JSON/CSV")
    parser.add_argument("--output", type=Path, help="Write unified JSON report")
    args = parser.parse_args()

    if not args.exports.is_dir():
        print(f"ERROR: exports directory not found: {args.exports}", file=sys.stderr)
        return 1

    try:
        report = run_engine(args.exports, args.timeline)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    output_json = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_json + "\n", encoding="utf-8")
        print(f"GRAVEYARD engine report: {args.output}")
    else:
        print(output_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
