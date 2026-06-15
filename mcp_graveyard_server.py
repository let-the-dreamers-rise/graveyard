#!/usr/bin/env python3
"""
GRAVEYARD — thin MCP server (FIND EVIL Pattern #2 — 8 read-only tools).

Exposes typed tools over stdio MCP — no shell access.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from mcp.server.fastmcp import FastMCP

from graveyard_engine import check_timeline_parity, correlate, run_engine
from scripts.benchmark_accuracy import run_benchmark
from scripts.generate_audit_log import generate_log
from spoliation_guard import spoliation_check
from verify_findings import load_findings
from verify_findings import verify_findings as run_verifier_checks

mcp = FastMCP(
    "graveyard",
    instructions=(
        "GRAVEYARD ghost-artifact tools for Protocol SIFT memory triage. "
        "Read-only: correlates Volatility exports, verifies finding citations, "
        "benchmarks accuracy, checks spoliation policy. No shell, no evidence writes."
    ),
)


def _resolve(path_str: str) -> Path:
    p = Path(path_str).expanduser().resolve()
    if not p.exists():
        raise ValueError(f"Path not found: {path_str}")
    return p


@mcp.tool(name="graveyard_correlate")
def mcp_graveyard_correlate(exports_dir: str) -> dict[str, Any]:
    """Detect ghost processes (psscan minus pslist) and orphan ESTABLISHED sockets."""
    exports = _resolve(exports_dir)
    if not exports.is_dir():
        raise ValueError(f"exports_dir must be a directory: {exports_dir}")
    report = correlate(exports)
    report.pop("_pslist_images", None)
    return report


@mcp.tool(name="graveyard_engine")
def mcp_graveyard_engine(exports_dir: str, timeline_path: str | None = None) -> dict[str, Any]:
    """Unified engine report: ghosts, orphans, timeline parity, contradictions, severity scores."""
    exports = _resolve(exports_dir)
    if not exports.is_dir():
        raise ValueError(f"exports_dir must be a directory: {exports_dir}")
    timeline = _resolve(timeline_path) if timeline_path else None
    return run_engine(exports, timeline)


@mcp.tool(name="verify_findings")
def mcp_verify_findings(findings_path: str, exports_dir: str) -> dict[str, Any]:
    """Verify findings JSON against export citations. Blocks report on failure."""
    findings_file = _resolve(findings_path)
    exports = _resolve(exports_dir)
    if not exports.is_dir():
        raise ValueError(f"exports_dir must be a directory: {exports_dir}")

    findings = load_findings(findings_file)
    _, errors = run_verifier_checks(findings, exports)
    return {
        "passed": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "finding_ids": [f.get("id") for f in findings],
        "findings_path": str(findings_file),
        "exports_dir": str(exports),
    }


@mcp.tool(name="benchmark_accuracy")
def mcp_benchmark_accuracy(
    exports_dir: str,
    ground_truth_path: str,
    findings_path: str | None = None,
) -> dict[str, Any]:
    """Score correlate + findings vs ground truth JSON; returns precision/recall/F1/FPR."""
    exports = _resolve(exports_dir)
    if not exports.is_dir():
        raise ValueError(f"exports_dir must be a directory: {exports_dir}")

    gt_file = _resolve(ground_truth_path)
    findings_file = _resolve(findings_path) if findings_path else None

    return run_benchmark(exports, gt_file, findings_file)


@mcp.tool(name="run_timeline_parity")
def mcp_run_timeline_parity(exports_dir: str, timeline_path: str) -> dict[str, Any]:
    """Cross-check memory ghosts against disk timeline JSON/CSV; includes contradiction report."""
    exports = _resolve(exports_dir)
    timeline = _resolve(timeline_path)
    if not exports.is_dir():
        raise ValueError(f"exports_dir must be a directory: {exports_dir}")
    return check_timeline_parity(exports, timeline)


@mcp.tool(name="generate_audit_log")
def mcp_generate_audit_log(exports_dir: str, case_id: str = "CASE-001") -> dict[str, Any]:
    """Return sha256 JSONL audit events for all files in exports/ (does not write to disk)."""
    exports = _resolve(exports_dir)
    if not exports.is_dir():
        raise ValueError(f"exports_dir must be a directory: {exports_dir}")
    events = generate_log(exports, case_id)
    return {
        "case_id": case_id,
        "exports_dir": str(exports),
        "event_count": len(events),
        "events": events,
    }


@mcp.tool(name="get_finding_schema")
def mcp_get_finding_schema() -> dict[str, Any]:
    """Return the GRAVEYARD finding JSON schema for agent drafting."""
    schema_path = _REPO / "schema" / "finding.schema.json"
    if not schema_path.exists():
        raise ValueError("schema/finding.schema.json not found")
    return json.loads(schema_path.read_text(encoding="utf-8"))


@mcp.tool(name="spoliation_check")
def mcp_spoliation_check(path: str, operation: str = "write") -> dict[str, Any]:
    """Check whether a path is allowed for read/write under GRAVEYARD spoliation policy."""
    if operation not in ("read", "write"):
        raise ValueError("operation must be 'read' or 'write'")
    return spoliation_check(path, operation)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
