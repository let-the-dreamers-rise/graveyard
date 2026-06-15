#!/usr/bin/env python3
"""
GRAVEYARD — deterministic self-correction: rebuild findings from engine facts only.

No LLM. Strips failed findings and regenerates observation/citations from engine report.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from graveyard_engine import run_engine  # noqa: E402


def build_findings_from_engine(report: dict) -> list[dict]:
    findings: list[dict] = []
    idx = 1
    ts = datetime.now(timezone.utc).isoformat()

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
                "command": "graveyard_engine.py; auto_correct_findings.py",
                "timestamp": ts,
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
            "interpretation": "Orphan socket — network connection without active process listing.",
            "confidence": "inferred",
            "citations": [
                {
                    "export_file": cite.get("export_file", "netscan_*.txt"),
                    "matched_text": cite.get("matched_text", str(orphan["pid"])),
                }
            ],
            "tool_provenance": {
                "command": "graveyard_engine.py; auto_correct_findings.py",
                "timestamp": ts,
            },
        })
        idx += 1

    for contra in report.get("contradictions", []):
        findings.append({
            "id": f"F{idx:03d}",
            "observation": (
                f"PID {contra['pid']} ({contra.get('memory_image', 'unknown')}) appears in "
                "pslist as running but is marked deleted on disk timeline export."
            ),
            "interpretation": (
                "Memory vs disk timeline contradiction — requires corroboration from "
                "additional disk artifacts."
            ),
            "confidence": "inferred",
            "citations": [],
            "tool_provenance": {
                "command": "graveyard_engine.py; auto_correct_findings.py",
                "timestamp": ts,
            },
        })
        idx += 1

    return findings


def inject_demo_bad_finding(findings: list[dict]) -> list[dict]:
    """Optional: prepend attribution violation for self-correction demo."""
    bad = {
        "id": "F000",
        "observation": "Process 1234 is malicious C2 beacon with attacker infrastructure",
        "interpretation": "Suspicious",
        "confidence": "confirmed",
        "citations": [
            {
                "export_file": "netscan_20240315.txt",
                "matched_text": "1234\t192.168.1.105\t203.0.113.5\t443\tESTABLISHED",
            }
        ],
        "tool_provenance": {
            "command": "agent_loop demo injection",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
    return [bad] + findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic findings self-correction from engine")
    parser.add_argument("--exports", type=Path, required=True)
    parser.add_argument("--timeline", type=Path, help="Optional disk timeline")
    parser.add_argument("--engine-report", type=Path, help="Use existing engine JSON instead of re-run")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--inject-bad", action="store_true", help="Inject attribution violation for demo")
    args = parser.parse_args()

    if args.engine_report and args.engine_report.exists():
        report = json.loads(args.engine_report.read_text(encoding="utf-8"))
    else:
        report = run_engine(args.exports, args.timeline)

    findings = build_findings_from_engine(report)
    if args.inject_bad:
        findings = inject_demo_bad_finding(findings)

    payload = {"findings": findings, "corrected_at": datetime.now(timezone.utc).isoformat()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Corrected findings written: {args.output} ({len(findings)} finding(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
