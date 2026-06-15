#!/usr/bin/env python3
"""
GRAVEYARD — deterministic finding verifier for Protocol SIFT.

Rejects findings whose claims are not provably grounded in ./exports/ tool output.
Exit 0 = all findings pass; exit 1 = rejections (agent must self-correct).
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

ATTRIBUTION_TERMS = (
    "exfiltrat",
    "attacker",
    "malicious",
    "compromised",
    "beacon",
    "c2",
    "command and control",
    "backdoor",
    "malware",
    "threat actor",
    "adversary",
    "exploit",
)

PHANTOM_PATTERNS = [
    (re.compile(r"\bPID\s+(\d+)\b", re.I), "pid"),
    (re.compile(r"\bPid\s+(\d+)\b"), "pid"),
    (re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b"), "ip"),
    (re.compile(r"([A-Za-z]:\\[^\s\"']+)"), "path"),
    (re.compile(r"(/[^\s\"']+)"), "path"),
]

REQUIRED_TOP_LEVEL = {"id", "observation", "interpretation", "confidence", "citations", "tool_provenance"}


def load_findings(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "findings" in data:
        findings = data["findings"]
    elif isinstance(data, list):
        findings = data
    else:
        raise ValueError("Expected a JSON array or object with 'findings' key")
    if not findings:
        raise ValueError("No findings to verify")
    return findings


def read_export(exports_dir: Path, export_file: str) -> str:
    candidate = Path(export_file)
    if not candidate.is_absolute():
        candidate = exports_dir / candidate
        if not candidate.exists():
            candidate = exports_dir / Path(export_file).name
    if not candidate.exists():
        raise FileNotFoundError(str(candidate))
    return candidate.read_text(encoding="utf-8", errors="replace")


def check_schema(finding: dict[str, Any], finding_idx: int) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_TOP_LEVEL - finding.keys()
    if missing:
        errors.append(f"Finding #{finding_idx} ({finding.get('id', '?')}): missing fields {sorted(missing)}")
        return errors

    fid = finding["id"]
    if finding["confidence"] not in ("confirmed", "inferred", "speculative"):
        errors.append(f"{fid}: invalid confidence '{finding['confidence']}'")

    if not finding["citations"]:
        errors.append(f"{fid}: at least one citation required")

    for i, cite in enumerate(finding["citations"]):
        if not cite.get("export_file") or not cite.get("matched_text"):
            errors.append(f"{fid}: citation[{i}] missing export_file or matched_text")

    prov = finding.get("tool_provenance", {})
    if not prov.get("command") or not prov.get("timestamp"):
        errors.append(f"{fid}: tool_provenance requires command and timestamp")

    return errors


def check_attribution_guard(finding: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    obs_lower = finding["observation"].lower()
    for term in ATTRIBUTION_TERMS:
        if term in obs_lower:
            errors.append(
                f"{finding['id']}: ATTRIBUTION_GUARD — observation contains '{term}'; "
                "move intent/attribution to interpretation with lower confidence"
            )
            break
    return errors


def check_citations(finding: dict[str, Any], exports_dir: Path, export_cache: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for cite in finding["citations"]:
        export_file = cite["export_file"]
        matched = cite["matched_text"]
        try:
            if export_file not in export_cache:
                export_cache[export_file] = read_export(exports_dir, export_file)
            content = export_cache[export_file]
        except FileNotFoundError:
            errors.append(f"{finding['id']}: CITATION_MISSING — export not found: {export_file}")
            continue

        if matched not in content:
            preview = matched[:80] + ("..." if len(matched) > 80 else "")
            errors.append(
                f"{finding['id']}: CITATION_MISMATCH — matched_text not in {export_file}: '{preview}'"
            )
    return errors


def check_phantom_artifacts(finding: dict[str, Any], all_exports_text: str) -> list[str]:
    errors: list[str] = []
    obs = finding["observation"]
    seen: set[str] = set()

    for pattern, kind in PHANTOM_PATTERNS:
        for match in pattern.finditer(obs):
            token = match.group(1) if match.lastindex else match.group(0)
            key = f"{kind}:{token}"
            if key in seen:
                continue
            seen.add(key)

            if kind == "path" and len(token) < 4:
                continue
            if kind == "ip" and token.startswith("0."):
                continue

            if token not in all_exports_text:
                errors.append(
                    f"{finding['id']}: PHANTOM_ARTIFACT — {kind.upper()} '{token}' in observation "
                    "but not found in any export file"
                )
    return errors


def check_confidence_consistency(finding: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if finding["confidence"] != "confirmed":
        return errors

    unique_exports = {c["export_file"] for c in finding["citations"]}
    if len(finding["citations"]) < 2 and len(unique_exports) < 2:
        errors.append(
            f"{finding['id']}: CONFIDENCE_GUARD — 'confirmed' requires 2+ citations "
            "from independent tool exports"
        )
    return errors


def verify_findings(findings: list[dict[str, Any]], exports_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    all_errors: list[str] = []
    export_cache: dict[str, str] = {}
    all_exports_text = ""

    for export_path in sorted(exports_dir.glob("*")):
        if export_path.is_file():
            try:
                all_exports_text += export_path.read_text(encoding="utf-8", errors="replace") + "\n"
            except OSError:
                pass

    for idx, finding in enumerate(findings, start=1):
        all_errors.extend(check_schema(finding, idx))
        if not finding.get("id"):
            continue
        all_errors.extend(check_attribution_guard(finding))
        all_errors.extend(check_citations(finding, exports_dir, export_cache))
        all_errors.extend(check_phantom_artifacts(finding, all_exports_text))
        all_errors.extend(check_confidence_consistency(finding))

    return findings, all_errors


def write_report(findings: list[dict[str, Any]], report_path: Path, case_id: str = "CASE-001") -> None:
    lines = [
        f"# Incident Response Report — {case_id}",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "All findings below passed GRAVEYARD verification.",
        "",
    ]

    for f in findings:
        lines.extend([
            f"## {f['id']} [{f['confidence'].upper()}]",
            "",
            "**Observation (tool-grounded):**",
            f["observation"],
            "",
            "**Interpretation (analyst inference):**",
            f["interpretation"],
            "",
            "**Evidence citations:**",
        ])
        for c in f["citations"]:
            lines.append(f"- `{c['export_file']}` → \"{c['matched_text'][:120]}\"")
        lines.extend([
            "",
            f"**Tool:** `{f['tool_provenance']['command']}` @ {f['tool_provenance']['timestamp']}",
            "",
            "---",
            "",
        ])

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def append_audit_log(log_path: Path, event: dict[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify IR findings against export citations")
    parser.add_argument("findings_file", type=Path, help="JSON file with findings array or {findings: [...]}")
    parser.add_argument("--exports", type=Path, default=Path("./exports"), help="Directory of raw tool exports")
    parser.add_argument("--report", type=Path, default=Path("./reports/report.md"), help="Output report path")
    parser.add_argument("--audit-log", type=Path, default=Path("./docs/execution_logs/verifier.jsonl"))
    parser.add_argument("--case-id", default="CASE-001")
    parser.add_argument("--json-out", action="store_true", help="Emit rejection reasons as JSON")
    args = parser.parse_args()

    if not args.findings_file.exists():
        print(f"ERROR: findings file not found: {args.findings_file}", file=sys.stderr)
        return 1

    if not args.exports.is_dir():
        print(f"ERROR: exports directory not found: {args.exports}", file=sys.stderr)
        return 1

    try:
        findings = load_findings(args.findings_file)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    _, errors = verify_findings(findings, args.exports)
    ts = datetime.now(timezone.utc).isoformat()

    event = {
        "timestamp": ts,
        "event": "verify_findings",
        "findings_file": str(args.findings_file),
        "finding_ids": [f.get("id") for f in findings],
        "passed": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "exports_dir": str(args.exports),
    }
    append_audit_log(args.audit_log, event)

    if errors:
        if args.json_out:
            print(json.dumps({"passed": False, "errors": errors}, indent=2))
        else:
            print("REJECTED — GRAVEYARD verification failed:\n", file=sys.stderr)
            for err in errors:
                print(f"  • {err}", file=sys.stderr)
            print("\nAgent action: fix findings or re-run tools, then resubmit.", file=sys.stderr)
        return 1

    write_report(findings, args.report, args.case_id)
    print(f"PASSED — {len(findings)} finding(s) verified. Report: {args.report}")
    append_audit_log(args.audit_log, {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "report_generated",
        "report_path": str(args.report),
        "report_sha256": sha256_file(args.report) if args.report.exists() else None,
        "finding_ids": [f["id"] for f in findings],
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
