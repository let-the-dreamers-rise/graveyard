#!/usr/bin/env python3
"""
GRAVEYARD — thin MCP server (FIND EVIL Pattern #2 lite).

Exposes read-only, typed tools over stdio MCP — no shell access:
  - graveyard_correlate(exports_dir)
  - verify_findings(findings_path, exports_dir)
  - benchmark_accuracy(exports_dir, ground_truth_path, findings_path?)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from mcp.server.fastmcp import FastMCP

from graveyard_correlate import correlate
from scripts.benchmark_accuracy import run_benchmark
from verify_findings import load_findings
from verify_findings import verify_findings as run_verifier_checks

mcp = FastMCP(
    "graveyard",
    instructions=(
        "GRAVEYARD ghost-artifact tools for Protocol SIFT memory triage. "
        "Read-only: correlates Volatility exports and verifies finding citations. "
        "No shell, no evidence writes."
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
    return correlate(exports)


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
    """Score correlate + findings vs ground truth JSON; returns precision/recall/F1 for judges."""
    exports = _resolve(exports_dir)
    if not exports.is_dir():
        raise ValueError(f"exports_dir must be a directory: {exports_dir}")

    gt_file = _resolve(ground_truth_path)
    findings_file = _resolve(findings_path) if findings_path else None

    return run_benchmark(exports, gt_file, findings_file)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
