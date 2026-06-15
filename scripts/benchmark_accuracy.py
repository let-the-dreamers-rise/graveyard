#!/usr/bin/env python3
"""
GRAVEYARD — benchmark accuracy: score correlate + findings vs ground truth JSON.

Outputs precision/recall/F1 and hallucination catch rate for judges.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from graveyard_correlate import correlate
from verify_findings import verify_findings


def load_ground_truth(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_findings(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "findings" in data:
        return data["findings"]
    if isinstance(data, list):
        return data
    raise ValueError("Findings must be array or {findings: [...]}")


def score_correlate(report: dict[str, Any], gt: dict[str, Any]) -> dict[str, Any]:
    expected = gt.get("expected_correlate", {})
    exp_ghosts = {(g["pid"], g.get("image", "").lower()) for g in expected.get("ghost_processes", [])}
    exp_orphans = {
        (o["pid"], o.get("foreign_address", ""), o.get("foreign_port", ""))
        for o in expected.get("orphan_sockets", [])
    }

    det_ghosts = {(g["pid"], g.get("image", "").lower()) for g in report.get("ghosts", [])}
    det_orphans = {
        (o["pid"], o.get("foreign_address", ""), o.get("foreign_port", ""))
        for o in report.get("orphan_sockets", [])
    }

    def prf(expected: set, detected: set) -> dict[str, float]:
        tp = len(expected & detected)
        fp = len(detected - expected)
        fn = len(expected - detected)
        precision = tp / (tp + fp) if (tp + fp) else 1.0
        recall = tp / (tp + fn) if (tp + fn) else 1.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        return {
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }

    ghost_metrics = prf(exp_ghosts, det_ghosts)
    orphan_metrics = prf(exp_orphans, det_orphans)

    return {
        "ghost_process": ghost_metrics,
        "orphan_socket": orphan_metrics,
        "expected_ghost_count": len(exp_ghosts),
        "detected_ghost_count": len(det_ghosts),
        "expected_orphan_count": len(exp_orphans),
        "detected_orphan_count": len(det_orphans),
    }


def score_findings(
    findings: list[dict[str, Any]],
    gt: dict[str, Any],
) -> dict[str, Any]:
    expected = gt.get("expected_findings", [])
    matched = 0
    details: list[dict[str, Any]] = []

    for exp in expected:
        tokens = [t.lower() for t in exp.get("required_observation_tokens", [])]
        found = False
        for f in findings:
            obs = f.get("observation", "").lower()
            if all(t in obs for t in tokens):
                found = True
                break
        details.append({
            "artifact_type": exp.get("artifact_type"),
            "pid": exp.get("pid"),
            "matched_in_findings": found,
        })
        if found:
            matched += 1

    total = len(expected) or 1
    return {
        "expected_finding_count": len(expected),
        "matched_finding_count": matched,
        "finding_recall": round(matched / total, 4),
        "details": details,
    }


def score_hallucinations(
    gt: dict[str, Any],
    exports_dir: Path,
) -> dict[str, Any]:
    tests = gt.get("hallucination_tests", [])
    caught = 0
    results: list[dict[str, Any]] = []

    for test in tests:
        finding = test["finding"]
        _, errors = verify_findings([finding], exports_dir)
        error_text = " ".join(errors)
        expected_codes = test.get("expected_reject_codes", [])
        codes_found = [c for c in expected_codes if c in error_text]
        rejected = len(errors) > 0
        if rejected:
            caught += 1
        results.append({
            "id": test.get("id"),
            "description": test.get("description"),
            "rejected": rejected,
            "error_count": len(errors),
            "expected_codes_matched": codes_found,
            "errors": errors,
        })

    total = len(tests) or 1
    return {
        "hallucination_tests": len(tests),
        "hallucinations_caught": caught,
        "hallucination_catch_rate": round(caught / total, 4),
        "details": results,
    }


def run_benchmark(
    exports_dir: Path,
    ground_truth_path: Path,
    findings_path: Path | None = None,
) -> dict[str, Any]:
    gt = load_ground_truth(ground_truth_path)
    report = correlate(exports_dir)

    metrics: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "case_id": gt.get("case_id", "unknown"),
        "exports_dir": str(exports_dir.resolve()),
        "ground_truth_file": ground_truth_path.name,
        "correlate": score_correlate(report, gt),
        "hallucination_guard": score_hallucinations(gt, exports_dir),
    }

    if findings_path and findings_path.exists():
        findings = load_findings(findings_path)
        metrics["findings"] = score_findings(findings, gt)
    else:
        metrics["findings"] = {"note": "No findings file provided — correlate-only benchmark"}

    baseline = gt.get("baseline_protocol_sift", {})
    g_recall = metrics["correlate"]["ghost_process"]["recall"]
    o_recall = metrics["correlate"]["orphan_socket"]["recall"]
    metrics["baseline_comparison"] = {
        "protocol_sift_estimated_ghost_recall": baseline.get("ghost_recall"),
        "protocol_sift_estimated_orphan_recall": baseline.get("orphan_recall"),
        "graveyard_ghost_recall": g_recall,
        "graveyard_orphan_recall": o_recall,
        "ghost_recall_delta": round(g_recall - baseline.get("ghost_recall", 0), 4),
        "orphan_recall_delta": round(o_recall - baseline.get("orphan_recall", 0), 4),
    }

    metrics["summary"] = {
        "ghost_recall": g_recall,
        "orphan_recall": o_recall,
        "ghost_precision": metrics["correlate"]["ghost_process"]["precision"],
        "orphan_precision": metrics["correlate"]["orphan_socket"]["precision"],
        "hallucination_catch_rate": metrics["hallucination_guard"]["hallucination_catch_rate"],
        "finding_recall": metrics["findings"].get("finding_recall"),
    }

    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark GRAVEYARD accuracy vs ground truth")
    parser.add_argument("--exports", type=Path, default=Path("examples/sample_exports"))
    parser.add_argument("--ground-truth", type=Path, default=Path("examples/ground_truth_srl2018_sample.json"))
    parser.add_argument("--findings", type=Path, help="Optional findings JSON to score")
    parser.add_argument("--output", type=Path, help="Write metrics JSON")
    args = parser.parse_args()

    if not args.exports.is_dir():
        print(f"ERROR: exports not found: {args.exports}", file=sys.stderr)
        return 1
    if not args.ground_truth.exists():
        print(f"ERROR: ground truth not found: {args.ground_truth}", file=sys.stderr)
        return 1

    metrics = run_benchmark(args.exports, args.ground_truth, args.findings)
    output_json = json.dumps(metrics, indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_json + "\n", encoding="utf-8")
        print(f"Benchmark metrics written: {args.output}")

    print(output_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
